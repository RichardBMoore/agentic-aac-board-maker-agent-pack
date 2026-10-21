"""QLearn client safety: token handling, least-privilege paths, unpublished-only writes (stubbed API, no network)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import types
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "qlearn-accessibility" / "scripts"
TOKEN = "4321~" + "Q" * 64  # synthetic; never a real credential


def load_module(filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


client_module = load_module("canvas_client.py", "canvas_client_tests")


class FakeResponse:
    def __init__(self, payload, link: str = "") -> None:
        self._body = payload if isinstance(payload, str) else json.dumps(payload)
        self.headers = {"Link": link}

    def read(self) -> bytes:
        return self._body.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


class FakeOpener:
    """Answers (method, path) pairs in order and records every request it sees."""

    def __init__(self, routes: list[tuple[str, str, object]]) -> None:
        self.routes = list(routes)
        self.requests: list[urllib.request.Request] = []

    def open(self, request: urllib.request.Request, timeout: float = 0):
        self.requests.append(request)
        path = request.full_url.split("?")[0].split("/api/v1", 1)[-1]
        for index, (method, expected, answer) in enumerate(self.routes):
            if method == request.get_method() and expected == path:
                del self.routes[index]
                if isinstance(answer, Exception):
                    raise answer
                return answer
        raise AssertionError(f"unexpected request {request.get_method()} {path}")

    def bodies(self) -> list[dict]:
        return [json.loads(request.data) for request in self.requests if request.data]


def http_error(code: int, body: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://qlearn.eq.edu.au/x", code, "error", {}, io.BytesIO(body.encode("utf-8")))


def make_client(routes, **kwargs):
    opener = FakeOpener(routes)
    sleeps: list[float] = []
    client = client_module.CanvasClient("https://qlearn.eq.edu.au", token_provider=lambda: TOKEN, opener=opener,
                                        sleep=sleeps.append, **kwargs)
    return client, opener, sleeps


class TokenHandlingTests(unittest.TestCase):
    def test_token_is_sent_as_bearer_header_only(self) -> None:
        client, opener, _ = make_client([("GET", "/users/self", FakeResponse({"name": "Test Teacher"}))])
        self.assertEqual("Test Teacher", client.whoami())
        request = opener.requests[0]
        self.assertEqual(f"Bearer {TOKEN}", request.get_header("Authorization"))
        self.assertNotIn(TOKEN, request.full_url)

    def test_errors_never_contain_the_token(self) -> None:
        echoed = f'{{"errors":[{{"message":"bad token Bearer {TOKEN} {TOKEN}"}}]}}'
        client, _, _ = make_client([("GET", "/courses/1/pages", http_error(500, echoed))])
        with self.assertRaises(client_module.QLearnError) as caught:
            client.list_pages("1")
        self.assertNotIn(TOKEN, str(caught.exception))
        self.assertNotIn("QQQQQQQQQQ", str(caught.exception))

    def test_401_explains_how_to_fix_it(self) -> None:
        client, _, _ = make_client([("GET", "/users/self", http_error(401, '{"errors":[{"message":"Invalid access token."}]}'))])
        with self.assertRaisesRegex(client_module.QLearnError, "make a new one"):
            client.whoami()

    def test_missing_token_gives_setup_instruction(self) -> None:
        fake_keyring = types.SimpleNamespace(get_password=lambda service, user: None)
        sys.modules["keyring"] = fake_keyring  # type: ignore[assignment]
        try:
            with self.assertRaisesRegex(client_module.QLearnError, "keyring set qlearn-token qlearn"):
                client_module.keyring_token()
        finally:
            del sys.modules["keyring"]

    def test_redirects_must_stay_on_https_qlearn_and_pass_the_policy(self) -> None:
        client, _, _ = make_client([])
        handler = client_module._SafeRedirect(client.check_policy)
        original = urllib.request.Request("https://qlearn.eq.edu.au/api/v1/courses/1/pages/a", headers={"Authorization": f"Bearer {TOKEN}"})
        for target in ("https://files.example-cdn.com/1",                       # another host
                       "http://qlearn.eq.edu.au/api/v1/courses/1/pages/b",      # downgrade to plain http
                       "https://qlearn.eq.edu.au/api/v1/courses/1/enrollments"):  # student data
            with self.subTest(target=target), self.assertRaises(urllib.error.HTTPError):
                handler.redirect_request(original, io.BytesIO(b""), 302, "Found", {}, target)
        followed = handler.redirect_request(original, io.BytesIO(b""), 302, "Found", {}, "https://qlearn.eq.edu.au/api/v1/courses/1/pages/b")
        self.assertEqual(f"Bearer {TOKEN}", followed.get_header("Authorization"))

    def test_base_url_cannot_point_anywhere_else(self) -> None:
        for base in ("https://evil.example.com", "http://qlearn.eq.edu.au", "https://qlearn.eq.edu.au.evil.example",
                     "https://qlearn.eq.edu.au:8443", "https://qlearn.eq.edu.au/sub"):
            with self.subTest(base=base), self.assertRaises(client_module.PolicyError):
                client_module.CanvasClient(base, token_provider=lambda: TOKEN)
        self.assertEqual("https://qed09.instructure.com", client_module.CanvasClient("https://qed09.instructure.com", token_provider=lambda: TOKEN).base_url)


class LeastPrivilegeTests(unittest.TestCase):
    def test_student_areas_are_refused_before_any_request(self) -> None:
        client, opener, _ = make_client([])
        # Documented Canvas endpoints that expose students, written independently of the client's own lists.
        for path in ("/courses/1/users", "/courses/1/enrollments", "/courses/1/enrollments.json",
                     "/courses/1/assignments/2/submissions", "/courses/1/assignments/2/gradeable_students",
                     "/courses/1/discussion_topics/3/entries", "/courses/1/discussion_topics/3/view", "/users/77",
                     "/users/self/activity_stream", "/users/self/profile", "/conversations", "/courses/1/recent_students",
                     "/courses/1/bulk_user_progress", "/courses/1/sections", "/courses/1/custom_gradebook_columns/3/data",
                     "/courses/1/quizzes/4/statistics", "/courses/1/quizzes/4/submissions", "/groups/5/memberships",
                     "/audit/grade_change/courses/1", "/courses/1/analytics/student_summaries",
                     "/courses/1/gradebook_history/days", "/courses/1/students/submissions", "/courses/1/pages/a/revisions",
                     "/courses/1/../1/users", "/courses/1//users", "/courses/1/pages%2F..%2Fusers", "/courses/1/pages/"):
            with self.subTest(path=path), self.assertRaises(client_module.PolicyError):
                client.get(path)
        self.assertEqual([], opener.requests)

    def test_query_strings_cannot_pull_in_student_data(self) -> None:
        client, opener, _ = make_client([])
        for path, params in (("/courses/1/modules", {"student_id": "99"}), ("/courses/1/assignments", {"include[]": "submission"}),
                             ("/courses", {"include[]": "total_students"}), ("/courses/1/pages", {"user_id": "5"}),
                             ("/courses", {"enrollment_type": "student"})):
            with self.subTest(path=path, params=params), self.assertRaises(client_module.PolicyError):
                client.get(path, params)
        with self.assertRaises(client_module.PolicyError):
            client.list_pages("1/sections?include[]=students&x=")
        with self.assertRaises(client_module.PolicyError):
            client.get_page("1", "../users")
        self.assertEqual([], opener.requests)

    def test_course_content_and_page_names_are_allowed(self) -> None:
        client, _, _ = make_client([
            ("GET", "/courses/1/pages/grades", FakeResponse({"url": "grades", "title": "Grades explained", "published": True})),
            ("GET", "/courses/1/modules", FakeResponse([])),
        ])
        self.assertEqual("grades", client.get_page("1", "grades")["url"])
        self.assertEqual([], client.get_all("/courses/1/modules"))

    def test_other_hosts_and_plain_http_are_refused(self) -> None:
        client, opener, _ = make_client([])
        with self.assertRaises(client_module.PolicyError):
            client.get("https://evil.example.com/api/v1/users/self")
        with self.assertRaises(client_module.PolicyError):
            client_module.CanvasClient("http://qlearn.eq.edu.au", token_provider=lambda: TOKEN)
        self.assertEqual([], opener.requests)

    def test_only_unpublished_page_writes_are_possible(self) -> None:
        client, opener, _ = make_client([])
        marked = "Lesson [WORKING FILE]"
        refused = [
            ("POST", "/courses/1/assignments", {"assignment": {"name": "x"}}),
            ("DELETE", "/courses/1/pages/intro", None),
            ("PUT", "/courses/1/pages/intro", {"wiki_page": {"published": True}}),
            ("PUT", "/courses/1/pages/intro", {"wiki_page": {"published": False}}),
            ("POST", "/courses/1/pages", {"wiki_page": {"title": marked, "published": "true"}}),
            ("POST", "/courses/1/pages", {"wiki_page": {"title": marked, "published": "yes"}}),
            ("POST", "/courses/1/pages", {"wiki_page": {"title": marked, "body": "x"}}),
            ("POST", "/courses/1/pages", {"wiki_page": {"title": "No marker", "published": False}}),
            ("POST", "/courses/1/pages", {"wiki_page": {"title": marked, "published": False, "publish_at": "2026-11-01"}}),
            ("POST", "/courses/1/pages", {"wiki_page": {"title": marked, "published": False, "notify_of_update": True}}),
            ("POST", "/courses/1/pages", {"wiki_page": {"title": marked, "published": False}, "extra": 1}),
            ("PUT", "/courses/1/pages/intro", {"wiki_page": {"front_page": True}}),
            ("PUT", "/courses/1/pages/intro", {"wiki_page": {"title": "Renamed without marker"}}),
            ("POST", "/courses/1/modules/2/items", {"module_item": {"type": "Page"}}),
            ("POST", "/conversations", {"recipients": ["1"]}),
        ]
        for method, path, data in refused:
            with self.subTest(method=method, path=path), self.assertRaises(client_module.PolicyError):
                client.request(method, path, data=data)
        self.assertEqual([], opener.requests)

    def test_pagination_follows_next_links(self) -> None:
        page2 = "https://qlearn.eq.edu.au/api/v1/courses/1/pages?page=2&per_page=100"
        client, opener, _ = make_client([
            ("GET", "/courses/1/pages", FakeResponse([{"url": "a", "title": "A", "published": True}], f'<{page2}>; rel="next"')),
            ("GET", "/courses/1/pages", FakeResponse([{"url": "b", "title": "B", "published": False}])),
        ])
        self.assertEqual(["a", "b"], [page["url"] for page in client.list_pages("1")])
        self.assertIn("per_page=100", opener.requests[0].full_url)

    def test_long_bookmark_pages_and_everyday_searches_are_allowed(self) -> None:
        bookmark = "bookmark:" + "WyJBIHZlcnkgbG9uZyB1bml0IHRpdGxlIGFib3V0IHBlcnN1YXNpdmUgbGFuZ3VhZ2UiLDEyMzQ1Nl0" * 3
        next_url = f"https://qlearn.eq.edu.au/api/v1/courses/1/pages?page={bookmark}&per_page=100&sort=title"
        client, opener, _ = make_client([
            ("GET", "/courses/1/pages", FakeResponse([{"url": "a", "title": "A", "published": True}], f'<{next_url}>; rel="next"')),
            ("GET", "/courses/1/pages", FakeResponse([{"url": "b", "title": "B", "published": True}])),
            ("GET", "/courses/1/pages", FakeResponse([])),
        ])
        self.assertEqual(["a", "b"], [page["url"] for page in client.list_pages("1")])
        self.assertEqual([], client.get_all("/courses/1/pages", {"search_term": "Teacher's notes & rubric"}))
        for bad in ("bookmark:abc;drop", "x" * 300):
            with self.subTest(page=bad), self.assertRaises(client_module.PolicyError):
                client.get("/courses/1/pages", {"page": bad})

    def test_rate_limit_is_retried_with_backoff(self) -> None:
        client, opener, sleeps = make_client([
            ("GET", "/users/self", http_error(403, "403 Forbidden (Rate Limit Exceeded)")),
            ("GET", "/users/self", FakeResponse({"name": "Test Teacher"})),
        ])
        self.assertEqual("Test Teacher", client.whoami())
        self.assertEqual([1], sleeps)


class WorkingCopyTests(unittest.TestCase):
    SOURCE = {"url": "unit-overview", "title": "Unit overview", "published": True, "body": "<p>Original</p>"}

    def test_create_requires_teacher_confirmation(self) -> None:
        client, opener, _ = make_client([])
        with self.assertRaisesRegex(client_module.PolicyError, "Ask the teacher first"):
            client.create_working_copy("1", "unit-overview", "<p>New</p>")
        self.assertEqual([], opener.requests)

    def test_create_makes_a_separate_unpublished_page_and_reads_it_back(self) -> None:
        created = {"url": "unit-overview-working-file", "title": "Unit overview [WORKING FILE]", "published": False}
        client, opener, _ = make_client([
            ("GET", "/courses/1/pages/unit-overview", FakeResponse(self.SOURCE)),
            ("POST", "/courses/1/pages", FakeResponse(created)),
            ("GET", "/courses/1/pages/unit-overview-working-file", FakeResponse({**created, "body": "<p>New</p>"})),
        ])
        saved = client.create_working_copy("1", "unit-overview", "<p>New</p>", confirmed=True)
        self.assertEqual("<p>New</p>", saved["body"])
        posted = opener.bodies()[0]["wiki_page"]
        self.assertIs(False, posted["published"])
        self.assertEqual("Unit overview [WORKING FILE]", posted["title"])
        self.assertEqual(["GET", "POST", "GET"], [request.get_method() for request in opener.requests])

    def test_create_stops_loudly_if_the_copy_is_published(self) -> None:
        created = {"url": "copy", "title": "Unit overview [WORKING FILE]", "published": False}
        client, _, _ = make_client([
            ("GET", "/courses/1/pages/unit-overview", FakeResponse(self.SOURCE)),
            ("POST", "/courses/1/pages", FakeResponse(created)),
            ("GET", "/courses/1/pages/copy", FakeResponse({**created, "published": True})),
        ])
        with self.assertRaisesRegex(client_module.QLearnError, "Safety stop"):
            client.create_working_copy("1", "unit-overview", "<p>New</p>", confirmed=True)

    def test_raw_put_to_a_published_original_is_refused(self) -> None:
        client, opener, _ = make_client([("GET", "/courses/1/pages/unit-overview", FakeResponse(self.SOURCE))])
        with self.assertRaisesRegex(client_module.PolicyError, "published"):
            client.request("PUT", "/courses/1/pages/unit-overview", data={"wiki_page": {"body": "<p>x</p>"}})
        self.assertEqual(["GET"], [request.get_method() for request in opener.requests])

    def test_update_refuses_published_or_unmarked_pages(self) -> None:
        client, opener, _ = make_client([
            ("GET", "/courses/1/pages/unit-overview", FakeResponse(self.SOURCE)),
            ("GET", "/courses/1/pages/draft", FakeResponse({"url": "draft", "title": "Draft", "published": False})),
        ])
        with self.assertRaisesRegex(client_module.PolicyError, "published"):
            client.update_working_copy("1", "unit-overview", "<p>x</p>", confirmed=True)
        with self.assertRaisesRegex(client_module.PolicyError, r"\[WORKING FILE\]"):
            client.update_working_copy("1", "draft", "<p>x</p>", confirmed=True)
        self.assertNotIn("PUT", [request.get_method() for request in opener.requests])

    def test_update_changes_only_the_body_of_a_working_file(self) -> None:
        page = {"url": "copy", "title": "Unit overview [WORKING FILE]", "published": False}
        client, opener, _ = make_client([
            ("GET", "/courses/1/pages/copy", FakeResponse(page)),
            ("PUT", "/courses/1/pages/copy", FakeResponse(page)),
            ("GET", "/courses/1/pages/copy", FakeResponse({**page, "body": "<p>v2</p>"})),
        ])
        saved = client.update_working_copy("1", "copy", "<p>v2</p>", confirmed=True)
        self.assertEqual("<p>v2</p>", saved["body"])
        self.assertEqual({"wiki_page": {"body": "<p>v2</p>"}}, opener.bodies()[0])

    def test_command_line_write_without_confirm_stops(self) -> None:
        body = ROOT / "tests" / "fixtures" / "qlearn" / "synthetic-lesson-page.html"
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            code = client_module.main(["create-working-copy", "1", "unit-overview", str(body)])
        self.assertEqual(2, code)
        self.assertIn("Ask the teacher first", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
