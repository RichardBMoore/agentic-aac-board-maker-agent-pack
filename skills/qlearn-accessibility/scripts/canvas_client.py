#!/usr/bin/env python3
"""Least-privilege QLearn (Canvas REST API) client for course-content work.

Safety model (enforced in code, not just in instructions):

- The access token is read from the operating system's password vault
  (Python ``keyring``: macOS Keychain, Windows Credential Manager) at the
  moment of each request. It is never accepted on the command line, printed,
  logged, written to disk or included in error messages.
- Requests go only to the two QLearn hosts (hard-coded) over HTTPS. Redirects
  are followed only if they stay on HTTPS, on QLearn, and pass the same checks.
- **Allowlist, not denylist.** Only named course-content routes can be read
  (your own name, your course list, course pages, modules, assignment/quiz
  descriptions, discussion topics, files, folders, tabs), with a small set of
  query parameters. Everything else (enrolments, users, submissions, grades,
  discussion replies, messages, analytics, statistics, groups...) is refused
  before anything is sent.
- The only writes: creating a new **unpublished** page titled ``[WORKING FILE]``,
  and changing the title/body of a page that is unpublished and titled
  ``[WORKING FILE]`` (checked against QLearn before every update). Payload keys
  are allowlisted, so nothing can publish, schedule publishing, notify, delete,
  message, grade or touch enrolments.
- Writes need ``confirmed=True`` (``--confirm`` on the command line), which an
  agent passes only after the teacher has said yes to that specific change.

Set up the token once (the agent opens this for the teacher; paste once, press Return):

    python3 -m keyring set qlearn-token qlearn

Commands:

    python3 canvas_client.py whoami
    python3 canvas_client.py courses
    python3 canvas_client.py pages COURSE_ID
    python3 canvas_client.py get-page COURSE_ID PAGE_URL --out page.html
    python3 canvas_client.py create-working-copy COURSE_ID SOURCE_PAGE_URL body.html --confirm --saved-out saved.html
    python3 canvas_client.py update-working-copy COURSE_ID PAGE_URL body.html --confirm --saved-out saved.html

Configuration (environment variables, all optional):
    QLEARN_BASE_URL          https://qlearn.eq.edu.au (default) or https://qed09.instructure.com; nothing else
    QLEARN_KEYRING_SERVICE   default qlearn-token
    QLEARN_KEYRING_USER      default qlearn
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

DEFAULT_BASE_URL = "https://qlearn.eq.edu.au"
ALLOWED_HOSTS = frozenset({"qlearn.eq.edu.au", "qed09.instructure.com"})  # hard-coded on purpose
WORKING_MARKER = "[WORKING FILE]"
ID = r"\d+(?:~\d+)?"
SLUG = r"[A-Za-z0-9_%-]+"
ID_RE = re.compile(rf"^{ID}$")
SLUG_RE = re.compile(rf"^{SLUG}$")

# Course content only. Anything not listed is refused before a request is made.
GET_ROUTES = tuple(re.compile(rf"^/api/v1/{route}$") for route in (
    "users/self",
    "courses",
    rf"courses/{ID}",
    rf"courses/{ID}/tabs",
    rf"courses/{ID}/front_page",
    rf"courses/{ID}/pages",
    rf"courses/{ID}/pages/{SLUG}",
    rf"courses/{ID}/modules",
    rf"courses/{ID}/modules/{ID}",
    rf"courses/{ID}/modules/{ID}/items",
    rf"courses/{ID}/modules/{ID}/items/{ID}",
    rf"courses/{ID}/assignments",
    rf"courses/{ID}/assignments/{ID}",
    rf"courses/{ID}/quizzes",
    rf"courses/{ID}/quizzes/{ID}",
    rf"courses/{ID}/discussion_topics",
    rf"courses/{ID}/discussion_topics/{ID}",
    rf"courses/{ID}/files",
    rf"courses/{ID}/files/{ID}",
    rf"courses/{ID}/folders",
))
POST_PAGE = re.compile(rf"^/api/v1/courses/(?P<course>{ID})/pages$")
PUT_PAGE = re.compile(rf"^/api/v1/courses/(?P<course>{ID})/pages/(?P<page>{SLUG})$")
SAFE_QUERY_VALUE = re.compile(r"^[A-Za-z0-9:_=+.\- ]{0,120}$")
QUERY_VALUE_PATTERNS = {
    "page": re.compile(r"^(?:\d{1,6}|first|last|next|bookmark:[A-Za-z0-9_\-]+=*)$"),  # Canvas bookmarks can be long
    "per_page": re.compile(r"^\d{1,3}$"),
    "search_term": re.compile(r"^[^\x00-\x1f\x7f]{1,200}$"),  # everyday text, e.g. "Teacher's notes & rubric"
}
QUERY_RULES: dict[str, frozenset[str] | None] = {
    # None = any short safe value; a set = only these values.
    "per_page": None,
    "page": None,
    "sort": None,
    "order": None,
    "search_term": None,
    "enrollment_type": frozenset({"teacher", "ta", "designer"}),
    "state[]": frozenset({"available", "unpublished", "completed"}),
    "include[]": frozenset({"items", "content_details"}),
}
STUDENT_WORDS = ("enrollment", "student", "user", "submission", "grade", "entries", "entry", "conversation",
                 "analytics", "statistic", "progress", "group", "membership", "audit", "page_view", "custom_gradebook")
CREATE_KEYS = frozenset({"title", "body", "published"})
UPDATE_KEYS = frozenset({"title", "body"})
TOKEN_SHAPES = re.compile(r"\d{1,8}~[A-Za-z0-9]{20,}|Bearer\s+\S+", re.IGNORECASE)


class QLearnError(RuntimeError):
    """A QLearn request failed or was refused. Messages never contain the token."""


class PolicyError(QLearnError):
    """The request is outside what this client is allowed to do."""


def redact(text: str, secret: str | None = None) -> str:
    if secret:
        text = text.replace(secret, "[token removed]")
    return TOKEN_SHAPES.sub("[token removed]", text)


def keyring_token() -> str:
    try:
        import keyring  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        raise QLearnError("Python's keyring library is not installed. Run: python3 -m pip install --user keyring") from None
    service = os.environ.get("QLEARN_KEYRING_SERVICE", "qlearn-token")
    user = os.environ.get("QLEARN_KEYRING_USER", "qlearn")
    token = keyring.get_password(service, user)
    if not token:
        raise QLearnError(f"No QLearn token in the password vault (service '{service}'). Save one with: python3 -m keyring set {service} {user}")
    return token.strip()


class _SafeRedirect(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only if it stays on HTTPS, on QLearn, and passes the same policy."""

    def __init__(self, check: Callable[[str, str], None]) -> None:
        self.check = check

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401 - urllib signature
        try:
            self.check("GET", newurl)
        except PolicyError as error:
            raise urllib.error.HTTPError(req.full_url, code, f"redirect refused: {error}", headers, fp) from None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class CanvasClient:
    def __init__(
        self,
        base_url: str | None = None,
        *,
        token_provider: Callable[[], str] = keyring_token,
        opener: Any = None,
        sleep: Callable[[float], None] = time.sleep,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or os.environ.get("QLEARN_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        parsed = urllib.parse.urlparse(self.base_url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in ALLOWED_HOSTS or parsed.path or parsed.port:
            raise PolicyError(f"QLEARN_BASE_URL must be one of: {', '.join('https://' + host for host in sorted(ALLOWED_HOSTS))}")
        self.allowed_hosts = ALLOWED_HOSTS
        self._token_provider = token_provider
        self._opener = opener or urllib.request.build_opener(_SafeRedirect(self.check_policy))
        self._sleep = sleep
        self.timeout = timeout

    # ------------------------------------------------------------------ policy
    def _url(self, path_or_url: str, params: dict | None = None) -> str:
        url = path_or_url if path_or_url.startswith("https://") else f"{self.base_url}/api/v1/{path_or_url.lstrip('/')}"
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
        return url

    def check_policy(self, method: str, url: str, data: dict | None = None) -> None:
        """Refuse anything that is not an allowlisted course-content read or an unpublished working-file write."""
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in self.allowed_hosts or parsed.port not in (None, 443):
            raise PolicyError(f"Refusing to send the QLearn token to {parsed.scheme}://{parsed.hostname or url}")
        if parsed.username or parsed.password or parsed.fragment or parsed.params:
            raise PolicyError("Unexpected characters in the QLearn address")
        path = parsed.path
        if any(marker in path.lower() for marker in ("%2f", "%5c", "%2e", "//", "/./", "/../")) or path.endswith("/"):
            raise PolicyError("Encoded or relative path segments are not allowed")
        query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if method == "GET":
            if not any(route.match(path) for route in GET_ROUTES):
                lowered = path.lower()
                if any(word in lowered for word in STUDENT_WORDS):
                    raise PolicyError(f"{path} is student information or outside course content, which this tool never reads")
                raise PolicyError(f"{path} is not on the course-content allowlist")
            for key, value in query:
                rule = QUERY_RULES.get(key, False)
                if rule is False:
                    raise PolicyError(f"Query parameter '{key}' is not allowed")
                pattern = QUERY_VALUE_PATTERNS.get(key, SAFE_QUERY_VALUE)
                if not pattern.match(value) or (rule is not None and value not in rule):
                    raise PolicyError(f"Query value '{key}={value}' is not allowed")
            return
        if query:
            raise PolicyError("Writes may not carry query parameters")
        if method == "POST" and POST_PAGE.match(path):
            page = _wiki_page(data, CREATE_KEYS)
            if page.get("published") is not False:
                raise PolicyError("New pages must be created with published: false")
            if WORKING_MARKER not in str(page.get("title", "")):
                raise PolicyError(f"New pages must be titled with {WORKING_MARKER}")
            return
        if method == "PUT" and PUT_PAGE.match(path):
            page = _wiki_page(data, UPDATE_KEYS)
            if "title" in page and WORKING_MARKER not in str(page["title"]):
                raise PolicyError(f"A working copy must keep {WORKING_MARKER} in its title")
            return
        raise PolicyError(f"{method} {path} is not allowed; this tool only creates and updates unpublished working-file pages")

    # ------------------------------------------------------------------ transport
    def request(self, method: str, path_or_url: str, *, params: dict | None = None, data: dict | None = None) -> tuple[Any, str]:
        url = self._url(path_or_url, params)
        self.check_policy(method, url, data)
        if method == "PUT":
            self._require_working_copy(url)
        token = self._token_provider()
        body = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        attempts = 0
        while True:
            attempts += 1
            req = urllib.request.Request(url, data=body, method=method, headers=headers)
            try:
                with self._opener.open(req, timeout=self.timeout) as response:
                    raw = response.read().decode("utf-8")
                    link = response.headers.get("Link", "") or ""
                break
            except urllib.error.HTTPError as error:
                detail = redact(error.read().decode("utf-8", "replace")[:300], token)
                throttled = error.code == 429 or (error.code == 403 and "rate limit" in detail.lower())
                if throttled and attempts < 4:
                    self._sleep(2 ** (attempts - 1))
                    continue
                where = redact(url.split("?")[0], token)
                if error.code == 401:
                    raise QLearnError("QLearn did not accept the token (401). It may have expired or been deleted: make a new one and save it again.") from None
                if error.code == 403:
                    raise QLearnError(f"QLearn said you don't have permission (403) for {method} {where}.") from None
                if error.code == 404:
                    raise QLearnError(f"QLearn could not find {where} (404). Check the course id and page address.") from None
                raise QLearnError(f"QLearn replied {error.code} to {method} {where}: {detail}") from None
            except urllib.error.URLError as error:
                raise QLearnError(f"Could not reach QLearn: {redact(str(error.reason), token)}") from None
        if raw.startswith("while(1);"):
            raw = raw[len("while(1);"):]
        return (json.loads(raw) if raw.strip() else None), link

    def _require_working_copy(self, url: str) -> None:
        """Check with QLearn that the page about to be changed is an unpublished working file."""
        match = PUT_PAGE.match(urllib.parse.urlparse(url).path)
        if not match:
            raise PolicyError("Only course pages can be updated")
        current = self.get(f"/courses/{match.group('course')}/pages/{match.group('page')}")
        if current.get("published"):
            raise PolicyError("That page is published, so students can see it. Make a working copy instead of editing it.")
        if WORKING_MARKER not in (current.get("title") or ""):
            raise PolicyError(f"Only pages titled with {WORKING_MARKER} are updated by this tool.")

    def get(self, path: str, params: dict | None = None) -> Any:
        return self.request("GET", path, params=params)[0]

    def get_all(self, path: str, params: dict | None = None) -> list:
        params = dict(params or {})
        params.setdefault("per_page", 100)
        data, link = self.request("GET", path, params=params)
        if not isinstance(data, list):
            return data
        items = list(data)
        next_url = _next_link(link)
        while next_url:
            data, link = self.request("GET", next_url)
            items.extend(data or [])
            next_url = _next_link(link)
        return items

    # ------------------------------------------------------------------ course content
    def whoami(self) -> str:
        return (self.get("/users/self") or {}).get("name", "")

    def teaching_courses(self) -> list[dict]:
        courses = self.get_all("/courses", {"enrollment_type": "teacher", "state[]": ["available", "unpublished"]})
        return [{"id": course.get("id"), "name": course.get("name")} for course in courses]

    def list_pages(self, course_id: str) -> list[dict]:
        course_id = _course_id(course_id)
        pages = self.get_all(f"/courses/{course_id}/pages", {"sort": "title"})
        return [{"url": page.get("url"), "title": page.get("title"), "published": page.get("published")} for page in pages]

    def get_page(self, course_id: str, page_url: str) -> dict:
        return self.get(f"/courses/{_course_id(course_id)}/pages/{_page_slug(page_url)}")

    def create_working_copy(self, course_id: str, source_page_url: str, body_html: str, *, confirmed: bool = False) -> dict:
        """Create a NEW unpublished page titled '<source title> [WORKING FILE]'; read it back; return the saved page."""
        if not confirmed:
            raise PolicyError("Ask the teacher first, then call with confirmed=True (--confirm).")
        course_id = _course_id(course_id)
        source = self.get_page(course_id, source_page_url)
        title = f"{source.get('title', 'Untitled')} {WORKING_MARKER}".strip()
        created = self.request("POST", f"/courses/{course_id}/pages",
                               data={"wiki_page": {"title": title, "body": body_html, "published": False}})[0]
        if not created or created.get("url") == source.get("url"):
            raise QLearnError("QLearn did not create a separate page; the original was not changed.")
        saved = self.get_page(course_id, created["url"])
        if saved.get("published"):
            raise QLearnError(f"Safety stop: the new page {saved.get('url')} is published. Unpublish it in QLearn now.")
        return saved

    def update_working_copy(self, course_id: str, page_url: str, body_html: str, *, confirmed: bool = False) -> dict:
        """Replace the body of an unpublished working-file page only; read it back; return the saved page."""
        if not confirmed:
            raise PolicyError("Ask the teacher first, then call with confirmed=True (--confirm).")
        course_id, page_url = _course_id(course_id), _page_slug(page_url)
        # request() checks with QLearn that the page is unpublished and titled [WORKING FILE] before the PUT.
        self.request("PUT", f"/courses/{course_id}/pages/{page_url}", data={"wiki_page": {"body": body_html}})
        saved = self.get_page(course_id, page_url)
        if saved.get("published"):
            raise QLearnError(f"Safety stop: {page_url} is now published. Unpublish it in QLearn now.")
        return saved


def _wiki_page(data: Any, allowed_keys: frozenset[str]) -> dict:
    """Payload must be exactly {"wiki_page": {...allowed keys...}}; anything else (publish_at, notify...) is refused."""
    if not isinstance(data, dict) or set(data) != {"wiki_page"} or not isinstance(data["wiki_page"], dict):
        raise PolicyError('Page writes must look like {"wiki_page": {...}}')
    page = data["wiki_page"]
    extra = set(page) - allowed_keys
    if extra:
        raise PolicyError(f"Page fields {sorted(extra)} are not allowed (no publishing, scheduling or notifications)")
    return page


def _course_id(value: str) -> str:
    value = str(value).strip()
    if not ID_RE.match(value):
        raise PolicyError(f"'{value}' is not a course id (use the number from the course list)")
    return value


def _page_slug(value: str) -> str:
    value = str(value).strip()
    if not SLUG_RE.match(value):
        raise PolicyError(f"'{value}' is not a page address (use the address from the page list)")
    return value


def _next_link(header: str) -> str | None:
    for part in header.split(","):
        if 'rel="next"' in part:
            return part[part.find("<") + 1:part.find(">")]
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Least-privilege QLearn course-content client.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("whoami", help="show your QLearn name")
    sub.add_parser("courses", help="list your teaching courses (names and ids)")
    pages = sub.add_parser("pages", help="list a course's pages")
    pages.add_argument("course_id")
    get_page = sub.add_parser("get-page", help="save a page body to a local file")
    get_page.add_argument("course_id")
    get_page.add_argument("page_url")
    get_page.add_argument("--out", type=Path, required=True)
    for name in ("create-working-copy", "update-working-copy"):
        write = sub.add_parser(name, help=f"{name.replace('-', ' ')} (unpublished; needs --confirm)")
        write.add_argument("course_id")
        write.add_argument("page_url", help="source page (create) or the working copy (update)")
        write.add_argument("body", type=Path, help="HTML body to save")
        write.add_argument("--confirm", action="store_true", help="the teacher has said yes to this change")
        write.add_argument("--saved-out", type=Path, help="write the body QLearn saved here, for compare_saved_canvas_page.py")
    args = parser.parse_args(argv)

    try:
        client = CanvasClient()
        if args.command == "whoami":
            print(client.whoami())
        elif args.command == "courses":
            for course in client.teaching_courses():
                print(f"{course['id']}\t{course['name']}")
        elif args.command == "pages":
            for page in client.list_pages(args.course_id):
                state = "published" if page["published"] else "unpublished"
                print(f"{page['url']}\t{state}\t{page['title']}")
        elif args.command == "get-page":
            page = client.get_page(args.course_id, args.page_url)
            args.out.write_text(page.get("body") or "", encoding="utf-8")
            print(f"Saved '{page.get('title')}' ({'published' if page.get('published') else 'unpublished'}) to {args.out}")
        else:
            body = args.body.read_text(encoding="utf-8")
            action = client.create_working_copy if args.command == "create-working-copy" else client.update_working_copy
            saved = action(args.course_id, args.page_url, body, confirmed=args.confirm)
            if args.saved_out:
                args.saved_out.write_text(saved.get("body") or "", encoding="utf-8")
            print(f"Saved unpublished page '{saved.get('title')}' at {saved.get('html_url') or saved.get('url')}")
    except QLearnError as error:
        print(f"STOPPED: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
