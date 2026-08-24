#!/usr/bin/env python3
"""Dashboard static server with durable GitHub bake.

POST /bake  JSON {"data": {localStorageKey: value, ...}}
  - Rewrites the /*baked-data*/ seed script in dashboard.html
  - Writes localStorage_dump.json
  - Commits and pushes to origin

Also accepts the dashboard's existing /save and /move-cards POSTs
as no-op 200s so the UI does not spam console errors.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DASHBOARD = ROOT / "dashboard.html"
DUMP = ROOT / "localStorage_dump.json"
PORT = int(os.environ.get("PORT", "8080"))
GIT_LOCK = threading.Lock()

BAKE_START = "<script>/*baked-data*/(function(){try{var D="
BAKE_END = ';for(var k in D){if(localStorage.getItem(k)===null){localStorage.setItem(k,D[k]);}}}catch(e){}})();</script>'


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def bake_to_github(data: dict) -> dict:
    if not isinstance(data, dict) or not data:
        raise ValueError("expected non-empty data object")

    # localStorage values are always strings
    clean = {str(k): ("" if v is None else str(v)) for k, v in data.items()}

    html = DASHBOARD.read_text(encoding="utf-8")
    start = html.find(BAKE_START)
    if start < 0:
        raise RuntimeError("baked-data script not found in dashboard.html")
    obj_start = start + len(BAKE_START)
    end = html.find(BAKE_END, obj_start)
    if end < 0:
        raise RuntimeError("baked-data script end marker not found")

    payload = json.dumps(clean, ensure_ascii=False, separators=(",", ":"))
    new_html = html[:obj_start] + payload + html[end:]
    DASHBOARD.write_text(new_html, encoding="utf-8")
    DUMP.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with GIT_LOCK:
        status = _git("status", "--porcelain")
        if status.returncode != 0:
            raise RuntimeError(status.stderr.strip() or "git status failed")
        if not status.stdout.strip():
            return {"ok": True, "committed": False, "message": "already up to date"}

        add = _git("add", "dashboard.html", "localStorage_dump.json")
        if add.returncode != 0:
            raise RuntimeError(add.stderr.strip() or "git add failed")

        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        msg = f"Bake browser dashboard state ({stamp})."
        commit = _git(
            "commit",
            "-m",
            msg,
            "-m",
            "Persist phone/browser localStorage into dashboard.html and localStorage_dump.json for durable GitHub sync.",
        )
        if commit.returncode != 0:
            raise RuntimeError(commit.stderr.strip() or commit.stdout.strip() or "git commit failed")

        branch = _git("rev-parse", "--abbrev-ref", "HEAD")
        branch_name = (branch.stdout or "main").strip()
        push = _git("push", "-u", "origin", branch_name)
        if push.returncode != 0:
            raise RuntimeError(push.stderr.strip() or push.stdout.strip() or "git push failed")

        sha = _git("rev-parse", "--short", "HEAD")
        return {
            "ok": True,
            "committed": True,
            "branch": branch_name,
            "sha": (sha.stdout or "").strip(),
            "keys": len(clean),
        }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _json(self, code: int, body: dict):
        raw = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/bake":
                body = self._read_json()
                data = body.get("data") if isinstance(body, dict) else None
                result = bake_to_github(data)
                return self._json(200, result)
            if path in ("/save", "/move-cards"):
                # Acknowledge UI autosave hooks; durable path is /bake.
                length = int(self.headers.get("Content-Length") or "0")
                if length:
                    self.rfile.read(length)
                return self._json(200, {"ok": True, "ignored": True})
            return self._json(404, {"ok": False, "error": "not found"})
        except Exception as e:  # noqa: BLE001
            return self._json(500, {"ok": False, "error": str(e)})

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    # Avoid serving parent paths; stay in ROOT.
    os.chdir(ROOT)
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"dashboard server on http://127.0.0.1:{PORT}/dashboard.html", flush=True)
    print("POST /bake to persist localStorage into GitHub", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
