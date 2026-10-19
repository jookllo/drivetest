"""Real HTTP checks against the loopback-only, disposable production container.

Forwarded HTTPS headers simulate Traefik; cookies are forwarded explicitly
because this test does not terminate real TLS. Never target a live deployment.
"""
import http.client
from http.cookies import SimpleCookie
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

base, state_file, phase = sys.argv[1:]
url = urlsplit(base)
assert url.scheme == "http" and url.hostname == "127.0.0.1", "Local test container only"
cookies = {}


def request(path, expected=200, method="GET", data=None, forwarded=True):
    connection = http.client.HTTPConnection(url.hostname, url.port, timeout=15)
    headers = {"Accept": "application/json", "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items())}
    if forwarded:
        headers["X-Forwarded-Proto"] = "https"
    if data is not None:
        headers["Content-Type"] = "application/json"
    connection.request(method, path, json.dumps(data) if data is not None else None, headers)
    response = connection.getresponse()
    body = response.read().decode()
    response_headers = dict(response.getheaders())
    for key, value in response.getheaders():
        if key.lower() == "set-cookie":
            parsed = SimpleCookie()
            parsed.load(value)
            cookies.update({name: morsel.value for name, morsel in parsed.items()})
    assert response.status == expected, f"{method} {path}: expected {expected}, got {response.status}: {body[:250]}"
    connection.close()
    return body, {k.lower(): v for k, v in response_headers.items()}


if phase == "restarted":
    saved = json.loads(Path(state_file).read_text())
    cookies.update(saved["cookies"])
    body, _ = request("/api/v1/quiz-session")
    assert json.loads(body)["csrf_token"] == saved["csrf_token"], "Guest session lost on restart"
    print("Guest session survives container restart.")
else:
    request("/quiz", expected=308, forwarded=False)
    body, headers = request("/quiz?demo=1")
    assert 'id="quiz-demo-data"' not in body, "Production exposed demo fixtures"
    assert "max-age=" in headers.get("strict-transport-security", ""), "Missing HSTS"
    request("/mdosimimi")
    request("/admin", expected=404)
    request("/.env", expected=404)
    request("/assets/quiz/app.js")
    request("/assets/quiz/admin.js")
    request("/assets/quiz/quiz.css")
    request("/vendor/vue.global.prod.js")
    request("/up")
    request("/api/v1/classes")
    request("/api/v1/preview/signs", expected=404)
    request("/api/v1/admin/questions", expected=401)
    body, _ = request("/api/v1/signs")
    assert json.loads(body)["data"] == [], "Imported drafts leaked publicly"
    request("/api/v1/signs/r01-stop/image", expected=404)
    body, headers = request("/api/v1/quiz-session")
    session = json.loads(body)
    assert session["csrf_token"] and session["attempt"] is None
    assert "no-store" in headers.get("cache-control", ""), "Session response may be cached"
    request("/api/v1/admin/login", expected=419, method="POST", data={"email": "nobody@example.test", "password": "unused"})
    body, _ = request("/api/v1/quiz-session")
    assert json.loads(body)["csrf_token"] == session["csrf_token"]
    Path(state_file).write_text(json.dumps({"cookies": cookies, "csrf_token": session["csrf_token"]}))
    print("HTTP, HTTPS-proxy, CSRF, assets, draft privacy and session checks passed.")
