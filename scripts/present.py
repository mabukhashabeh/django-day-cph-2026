#!/usr/bin/env python3
"""Presenter: slides + a real bash PTY + file reads. Bind 127.0.0.1 only."""
from __future__ import annotations

import fcntl
import json
import os
import pty
import queue
import re
import select
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
SLIDES = ROOT / "slides"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PRESENT_PORT", "8777"))

SAFE_FILE = re.compile(
    r"^(catalog|scripts|fixtures|\.github)/[A-Za-z0-9._/-]+$"
    r"|^\.pre-commit-config\.yaml$"
    r"|^\.github/workflows/pre-commit\.yml$"
)

TREE = [
    ".pre-commit-config.yaml",
    ".github/workflows/pre-commit.yml",
    "catalog/views.py",
    "catalog/checks.py",
    "catalog/apps.py",
    "catalog/models.py",
]

JOBS = {
    "reset": ["bash", str(ROOT / "scripts/reset.sh")],
    "demo-1": ["bash", str(ROOT / "scripts/demo-1-secrets-and-breakpoint.sh")],
    "demo-2": ["bash", str(ROOT / "scripts/demo-2-django-check.sh")],
    "pass": ["bash", str(ROOT / "scripts/demo-pass.sh")],
    "skip": ["bash", str(ROOT / "scripts/demo-4-why-ci.sh")],
    "all-files": ["pre-commit", "run", "--all-files"],
}

LOCK = threading.Lock()
CURRENT: subprocess.Popen | None = None


def env() -> dict[str, str]:
    out = os.environ.copy()
    venv = ROOT / ".venv" / "bin"
    if venv.is_dir():
        out["PATH"] = str(venv) + os.pathsep + out.get("PATH", "")
    out["PYTHONUNBUFFERED"] = "1"
    out["TERM"] = "xterm-256color"
    out["PS1"] = r"\W $ "
    return out


def kill_current() -> None:
    global CURRENT
    with LOCK:
        proc = CURRENT
        CURRENT = None
    if proc and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


class Pty:
    def __init__(self) -> None:
        self.master: int | None = None
        self.proc: subprocess.Popen | None = None
        self.q: queue.Queue[bytes] = queue.Queue()
        self.alive = False

    def start(self) -> None:
        self.stop()
        master, slave = pty.openpty()
        self.proc = subprocess.Popen(
            ["/bin/bash", "--noprofile", "--norc", "-i"],
            cwd=str(ROOT),
            env=env(),
            stdin=slave,
            stdout=slave,
            stderr=slave,
            close_fds=True,
            preexec_fn=os.setsid,
        )
        os.close(slave)
        flags = fcntl.fcntl(master, fcntl.F_GETFL)
        fcntl.fcntl(master, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self.master = master
        self.alive = True
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self) -> None:
        assert self.master is not None
        while self.alive:
            try:
                ready, _, _ = select.select([self.master], [], [], 0.25)
            except (OSError, ValueError):
                break
            if not ready:
                if self.proc and self.proc.poll() is not None:
                    break
                continue
            try:
                data = os.read(self.master, 8192)
            except OSError:
                break
            if not data:
                break
            self.q.put(data)
        self.alive = False

    def write(self, data: bytes) -> None:
        if self.master is None:
            return
        os.write(self.master, data)

    def stop(self) -> None:
        self.alive = False
        if self.proc and self.proc.poll() is None:
            try:
                os.killpg(os.getpgid(self.proc.pid), 15)
            except OSError:
                self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self.master is not None:
            try:
                os.close(self.master)
            except OSError:
                pass
        self.master = None
        self.proc = None
        while not self.q.empty():
            try:
                self.q.get_nowait()
            except queue.Empty:
                break


PTY = Pty()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SLIDES), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s\n" % (fmt % args))

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else b""
        if parsed.path == "/api/kill":
            kill_current()
            self._json(200, {"ok": True})
            return
        if parsed.path == "/api/pty/start":
            PTY.start()
            self._json(200, {"ok": True})
            return
        if parsed.path == "/api/pty":
            if not PTY.alive:
                PTY.start()
            PTY.write(body)
            self._json(200, {"ok": True})
            return
        self._json(404, {"error": "not found"})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/interactive.html")
            self.end_headers()
            return
        if path == "/api/health":
            self._json(
                200,
                {
                    "ok": True,
                    "repo": str(ROOT),
                    "pty": PTY.alive,
                    "venv": (ROOT / ".venv" / "bin" / "pre-commit").exists(),
                },
            )
            return
        if path == "/api/tree":
            self._json(200, {"files": TREE})
            return
        if path == "/api/file":
            self._file(parse_qs(parsed.query).get("path", [""])[0])
            return
        if path == "/api/run":
            self._run(parse_qs(parsed.query).get("id", [""])[0])
            return
        if path == "/api/pty":
            self._pty_sse()
            return
        super().do_GET()

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Cache-Control", "no-store")

    def _json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _file(self, rel: str) -> None:
        rel = unquote(rel).lstrip("/")
        if not SAFE_FILE.match(rel):
            self._json(403, {"error": "path not allowed"})
            return
        target = (ROOT / rel).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            self._json(403, {"error": "path not allowed"})
            return
        if not target.is_file():
            self._json(404, {"error": "missing"})
            return
        self._json(
            200,
            {"path": rel, "text": target.read_text(encoding="utf-8", errors="replace")},
        )

    def _run(self, job_id: str) -> None:
        cmd = JOBS.get(job_id)
        if not cmd:
            self._json(400, {"error": "unknown job", "jobs": list(JOBS)})
            return
        kill_current()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self._cors()
        self.end_headers()
        self._sse({"kind": "start", "id": job_id, "cmd": " ".join(cmd)})
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env(),
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            self._sse({"kind": "line", "text": str(exc)})
            self._sse({"kind": "exit", "code": 1})
            return
        global CURRENT
        with LOCK:
            CURRENT = proc
        deadline = time.monotonic() + 90
        assert proc.stdout is not None
        code = 1
        try:
            while True:
                if time.monotonic() > deadline:
                    proc.kill()
                    self._sse({"kind": "line", "text": "timed out after 90s"})
                    break
                line = proc.stdout.readline()
                if line == "" and proc.poll() is not None:
                    break
                if line:
                    self._sse({"kind": "line", "text": line.rstrip("\n")})
            code = proc.wait(timeout=3)
        except BrokenPipeError:
            proc.kill()
            return
        except Exception as exc:  # noqa: BLE001
            self._sse({"kind": "line", "text": str(exc)})
            polled = proc.poll()
            code = polled if polled is not None else 1
        finally:
            with LOCK:
                if CURRENT is proc:
                    CURRENT = None
        self._sse({"kind": "exit", "code": int(code or 0)})

    def _pty_sse(self) -> None:
        if not PTY.alive:
            PTY.start()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self._cors()
        self.end_headers()
        try:
            while PTY.alive:
                try:
                    chunk = PTY.q.get(timeout=12)
                except queue.Empty:
                    self._sse({"ping": True})
                    continue
                self._sse({"t": chunk.decode("utf-8", "replace")})
        except BrokenPipeError:
            return

    def _sse(self, payload: dict) -> None:
        self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode())
        self.wfile.flush()


def main() -> int:
    if not SLIDES.is_dir():
        print("slides/ missing", file=sys.stderr)
        return 1
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/interactive.html"
    print("  Django Day CPH · presenter", flush=True)
    print(f"  {url}", flush=True)
    print("  T terminal · G GitHub", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        kill_current()
        PTY.stop()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
