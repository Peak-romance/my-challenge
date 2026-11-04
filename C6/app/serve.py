# -*- coding: utf-8 -*-
"""
单端口生产编排器（用于 WorkBuddy 发布 / 任意单端口部署）
------------------------------------------------------------------
对外只暴露一个 HTTP 端口（读取环境变量 PORT，默认 3000，绑定 0.0.0.0）：
  1. 在内部 127.0.0.1:8000 拉起 FastAPI 后端（uvicorn 子进程）；
  2. 在同一端口托管 frontend/ 静态站点，并把 /api、/uploads 反向代理到后端。

本地免 Docker 也可用：
    python serve.py                # 默认 3000
    PORT=8080 python serve.py
"""
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend"
BACKEND_PORT = 8000
PORT = int(os.environ.get("PORT", "3000"))
PROXY_PREFIXES = ("/api/", "/uploads/")
BACKEND_ORIGIN = f"http://127.0.0.1:{BACKEND_PORT}"


def start_backend() -> None:
    """内部子进程启动 FastAPI（仅监听回环，不对外暴露）"""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "backend")
    subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(BACKEND_PORT)],
        cwd=str(ROOT / "backend"),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class ProxyHandler(SimpleHTTPRequestHandler):
    """静态站点 + /api、/uploads 反代到内部后端"""

    def _proxy(self) -> None:
        target = BACKEND_ORIGIN + self.path
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {}
        for k in ("Authorization", "Content-Type", "Accept"):
            if self.headers.get(k):
                headers[k] = self.headers.get(k)
        req = urllib.request.Request(target, data=body, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = resp.read()
                self.send_response(resp.status)
                ct = resp.headers.get("Content-Type")
                if ct:
                    self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as e:
            payload = e.read()
            self.send_response(e.code)
            ct = e.headers.get("Content-Type") if e.headers else None
            if ct:
                self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def do_GET(self):
        if self.path.startswith(PROXY_PREFIXES):
            return self._proxy()
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith(PROXY_PREFIXES):
            return self._proxy()
        return super().do_POST()

    def do_PUT(self):
        if self.path.startswith(PROXY_PREFIXES):
            return self._proxy()
        return super().do_PUT()

    def do_DELETE(self):
        if self.path.startswith(PROXY_PREFIXES):
            return self._proxy()
        return super().do_DELETE()

    def do_PATCH(self):
        if self.path.startswith(PROXY_PREFIXES):
            return self._proxy()
        return super().do_PATCH()

    def log_message(self, *args):  # 静默访问日志
        pass


def wait_backend() -> bool:
    for _ in range(60):
        try:
            with urllib.request.urlopen(BACKEND_ORIGIN + "/api/health", timeout=5) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False


if __name__ == "__main__":
    start_backend()
    if not wait_backend():
        print("[serve] 后端启动失败", file=sys.stderr)
    os.chdir(str(FRONTEND))
    handler = partial(ProxyHandler, directory=str(FRONTEND))
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), handler)
    print(f"[serve] 平台已启动：http://0.0.0.0:{PORT}  (API 代理到 {BACKEND_ORIGIN})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
