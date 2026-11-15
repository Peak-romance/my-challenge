"""L1 接口层 · HTTP（可选）。

用标准库实现，零依赖。用于验证"同一内核可被多种接口驱动"这一分层主张：
本文件不包含任何规划/记忆/工具逻辑，只做协议适配。

启动：python agent.py --serve 8765
调用：curl -X POST http://127.0.0.1:8765/run -H "Content-Type: application/json" -d "{\"task\":\"生成今日简报\"}"
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ..core.loop import Agent


def serve(port: int = 8765) -> None:
    agent = Agent(verbose=False)

    class Handler(BaseHTTPRequestHandler):
        server_version = "C10Agent/1.0"

        def _send(self, code: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path in ("/", "/health", "/healthz"):
                self._send(200, {
                    "status": "ok",
                    "service": "C10 Second Brain",
                    "skills": [s.name for s in agent.skills.all()],
                    "tools": len(agent.tools.names()),
                    "stats": agent.memory.stats(),
                })
            else:
                self._send(404, {"error": "not found", "hint": "GET /health 或 POST /run"})

        def do_POST(self):  # noqa: N802
            if self.path != "/run":
                self._send(404, {"error": "not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(length) or b"{}")
                task = (data.get("task") or "").strip()
                if not task:
                    self._send(400, {"error": "task 不能为空"})
                    return
                res = agent.run(task, source="http", session=data.get("session", "http"))
                self._send(200, res.to_dict())
            except Exception as e:
                self._send(500, {"error": f"{type(e).__name__}: {e}"})

        def log_message(self, fmt, *args):  # 静默默认日志，避免污染控制台
            return

    print(f"[serve] http://127.0.0.1:{port}  GET /health  POST /run")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
