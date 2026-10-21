#!/usr/bin/env python3
"""Least-privilege QLearn (Canvas REST API) client for course-content work.

Safety model (enforced in code, not just in instructions):

- The access token is read from the operating system's password vault
  (Python ``keyring``: macOS Keychain, Windows Credential Manager) at the
  moment of each request. It is never accepted on the command line, printed,
  logged, written to disk or included in error messages.
- Requests go only to QLearn hosts over HTTPS. A redirect to any other host is
  followed without the token.
- Read-only by default. The only writes are creating a new **unpublished**
  page and updating an unpublished page whose title marks it as a working
  file. Nothing can publish, delete, message, grade or touch enrolments.
- Student areas are refused: enrolments, users, submissions, grades,
  discussion replies, conversations, analytics, page views.
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
    QLEARN_BASE_URL          default https://qlearn.eq.edu.au
    QLEARN_EXTRA_HOSTS       comma-separated extra hosts for the same QLearn (default adds qed09.instructure.com)
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
DEFAULT_EXTRA_HOSTS = ("qed09.instructure.com",)
WORKING_MARKER = "[WORKING FILE]"
COURSE_ID = r"(?:\d+|\d+~\d+|sis_course_id:[A-Za-z0-9_.-]+)"
PAGE_URL = r"[A-Za-z0-9_.~%-]+"

BLOCKED_SEGMENTS = {
    "enrollments", "students", "users", "submissions", "quiz_submissions", "submission_history", "grades",
    "gradebook_history", "gradebook", "analytics", "conversations", "entries", "entry_list", "view", "participants",
    "recipients", "search_users", "activity_stream", "page_views", "communication_channels", "peer_reviews",
    "outcome_results", "outcome_rollups", "student_summaries", "logins", "avatars", "observees", "messages",
}
WRITE_RULES: dict[str, list[re.Pattern[str]]] = {
    "POST": [re.compile(rf"^/api/v1/courses/{COURSE_ID}/pages$")],
    "PUT": [re.compile(rf"^/api/v1/courses/{COURSE_ID}/pages/{PAGE_URL}$")],
}
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


class _StripAuthOnForeignRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_hosts: set[str]) -> None:
        self.allowed_hosts = allowed_hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401 - urllib signature
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and (urllib.parse.urlparse(newurl).hostname or "").lower() not in self.allowed_hosts:
            new.remove_header("Authorization")
        return new


class CanvasClient:
    def __init__(
        self,
        base_url: str | None = None,
        *,
        extra_hosts: list[str] | None = None,
        token_provider: Callable[[], str] = keyring_token,
        opener: Any = None,
        sleep: Callable[[float], None] = time.sleep,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = (base_url or os.environ.get("QLEARN_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        parsed = urllib.parse.urlparse(self.base_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise PolicyError("QLEARN_BASE_URL must be an https:// address")
        hosts = extra_hosts if extra_hosts is not None else [
            host.strip() for host in os.environ.get("QLEARN_EXTRA_HOSTS", ",".join(DEFAULT_EXTRA_HOSTS)).split(",") if host.strip()
        ]
        self.allowed_hosts = {parsed.hostname.lower(), *(host.lower() for host in hosts)}
        self._token_provider = token_provider
        self._opener = opener or urllib.request.build_opener(_StripAuthOnForeignRedirect(self.allowed_hosts))
        self._sleep = sleep
        self.timeout = timeout

    # ------------------------------------------------------------------ policy
    def _url(self, path_or_url: str, params: dict | None = None) -> str:
        url = path_or_url if path_or_url.startswith("https://") else f"{self.base_url}/api/v1/{path_or_url.lstrip('/')}"
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
        return url

    def check_policy(self, method: str, url: str, data: dict | None = None) -> None:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in self.allowed_hosts:
            raise PolicyError(f"Refusing to send the QLearn token to {parsed.hostname or url}")
        path = urllib.parse.unquote(parsed.path)
        segments = [segment.lower() for segment in path.split("/") if segment]
        if segments[:2] != ["api", "v1"]:
            raise PolicyError("Only QLearn's /api/v1/ endpoints are used")
        rest = segments[2:]
        if rest[:2] == ["users", "self"]:
            if len(rest) > 2 and rest[2] not in {"courses", "profile"}:
                raise PolicyError("Only your own name and course list are read from /users/self")
            checked = rest[2:]
        else:
            # A page's own address (e.g. a page called "Grades") is a name, not a student area.
            checked = [segment for index, segment in enumerate(rest) if not (index > 0 and rest[index - 1] == "pages")]
        blocked = BLOCKED_SEGMENTS.intersection(checked)
        if blocked:
            raise PolicyError(f"'{sorted(blocked)[0]}' is student information, which this tool never reads")
        if method == "GET":
            return
        rules = WRITE_RULES.get(method)
        if not rules or not any(rule.match(path) for rule in rules):
            raise PolicyError(f"{method} {path} is not allowed; this tool only creates and updates unpublished pages")
        if data is not None and _would_publish(data):
            raise PolicyError("Publishing is not allowed. Pages are created and kept unpublished; publish in QLearn yourself.")

    # ------------------------------------------------------------------ transport
    def request(self, method: str, path_or_url: str, *, params: dict | None = None, data: dict | None = None) -> tuple[Any, str]:
        url = self._url(path_or_url, params)
        self.check_policy(method, url, data)
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
        pages = self.get_all(f"/courses/{course_id}/pages", {"sort": "title"})
        return [{"url": page.get("url"), "title": page.get("title"), "published": page.get("published")} for page in pages]

    def get_page(self, course_id: str, page_url: str) -> dict:
        return self.get(f"/courses/{course_id}/pages/{urllib.parse.quote(page_url, safe='')}")

    def create_working_copy(self, course_id: str, source_page_url: str, body_html: str, *, confirmed: bool = False,
                            marker: str = WORKING_MARKER) -> dict:
        """Create a NEW unpublished page titled '<source title> [WORKING FILE]'; read it back; return the saved page."""
        if not confirmed:
            raise PolicyError("Ask the teacher first, then call with confirmed=True (--confirm).")
        source = self.get_page(course_id, source_page_url)
        title = f"{source.get('title', 'Untitled')} {marker}".strip()
        created = self.request("POST", f"/courses/{course_id}/pages",
                               data={"wiki_page": {"title": title, "body": body_html, "published": False}})[0]
        if not created or created.get("url") == source.get("url"):
            raise QLearnError("QLearn did not create a separate page; the original was not changed.")
        saved = self.get_page(course_id, created["url"])
        if saved.get("published"):
            raise QLearnError(f"Safety stop: the new page {saved.get('url')} is published. Unpublish it in QLearn now.")
        return saved

    def update_working_copy(self, course_id: str, page_url: str, body_html: str, *, confirmed: bool = False,
                            marker: str = WORKING_MARKER) -> dict:
        """Replace the body of an unpublished working-file page only; read it back; return the saved page."""
        if not confirmed:
            raise PolicyError("Ask the teacher first, then call with confirmed=True (--confirm).")
        current = self.get_page(course_id, page_url)
        if current.get("published"):
            raise PolicyError("That page is published, so students can see it. Make a working copy instead of editing it.")
        if marker not in (current.get("title") or ""):
            raise PolicyError(f"Only pages titled with {marker} are updated by this tool.")
        self.request("PUT", f"/courses/{course_id}/pages/{urllib.parse.quote(page_url, safe='')}",
                     data={"wiki_page": {"body": body_html}})
        saved = self.get_page(course_id, page_url)
        if saved.get("published"):
            raise QLearnError(f"Safety stop: {page_url} is now published. Unpublish it in QLearn now.")
        return saved


def _would_publish(data: Any) -> bool:
    if isinstance(data, dict):
        for key, value in data.items():
            name = str(key).lower()
            if name.endswith("published") and str(value).lower() in {"true", "1"}:
                return True
            if name in {"event", "workflow_state"} and str(value).lower() in {"publish", "offer", "active", "available"}:
                return True
            if name in {"notify_of_update", "front_page"} and str(value).lower() in {"true", "1"}:
                return True
            if _would_publish(value):
                return True
    elif isinstance(data, list):
        return any(_would_publish(item) for item in data)
    return False


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
