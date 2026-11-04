# -*- coding: utf-8 -*-
"""
C9 二维码功能端到端验证脚本
------------------------------------------------------------------
1) 在临时库启动后端（自动建表 + 注入种子数据）
2) 调用 GET /api/assets/{id}/qrcode（公开接口）
3) 将返回 PNG 解码，核对内容是否为预期深链
4) 验证不存在资产返回 404
仅用于交付验证；cv2 为可选依赖（解码实证），缺失时退回结构校验。
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="c9_verify_")
PORT = 8211
BASE = f"http://127.0.0.1:{PORT}"
DB = os.path.join(TMP, "app.db")
UPLOADS = os.path.join(TMP, "uploads")

os.makedirs(os.path.dirname(DB), exist_ok=True)
os.makedirs(UPLOADS, exist_ok=True)

ENV = dict(os.environ)
ENV.update(
    {
        "DATABASE_PATH": DB,
        "UPLOAD_DIR": UPLOADS,
    }
)

passed = 0
failed = 0


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} {extra}")


def req(method, path, token=None):
    url = BASE + path
    headers = {}
    if token:
        headers["Authorization"] = "Bearer " + token
    r = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main():
    py = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
    if not os.path.exists(py):
        py = os.path.join(ROOT, ".venv", "bin", "python")
    proc = subprocess.Popen(
        [py, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=os.path.join(ROOT, "backend"),
        env=ENV,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        # 等待健康
        ok = False
        for _ in range(60):
            try:
                st, _ = req("GET", "/api/health")
                if st == 200:
                    ok = True
                    break
            except Exception:
                pass
            time.sleep(1)
        check("后端启动 /api/health=200", ok)
        if not ok:
            return

        # 登录管理员，取真实资产 id（公开 /api/assets 需登录，故用管理员接口）
        import json

        def post_json(path, payload):
            data = json.dumps(payload).encode("utf-8")
            r = urllib.request.Request(BASE + path, data=data,
                                       headers={"Content-Type": "application/json"},
                                       method="POST")
            try:
                with urllib.request.urlopen(r, timeout=30) as resp:
                    return resp.status, json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read().decode("utf-8"))

        token = None
        for cred in ({"username": "admin1", "password": "123456"},
                     {"username": "user1", "password": "123456"}):
            st, data = post_json("/api/auth/login", cred)
            if st == 200 and "token" in data:
                token = data["token"]
                break
        check("管理员登录成功", token is not None, f"login status={st}")

        assets = []
        if token:
            st, body = req("GET", "/api/admin/assets", token=token)
            if st == 200:
                try:
                    parsed = json.loads(body.decode("utf-8"))
                except Exception:
                    parsed = []
                # 兼容 {items:[...]} 与 [...] 两种结构
                if isinstance(parsed, list):
                    assets = parsed
                else:
                    assets = parsed.get("items", parsed.get("data", []))
        check("种子资产存在 (>=1)", len(assets) >= 1, f"got {len(assets)}")

        if assets:
            aid = assets[0]["id"]
            # 带 base 参数请求二维码
            base = "http://192.168.1.50:3000"
            st, png = req("GET", f"/api/assets/{aid}/qrcode?base={urllib.parse.quote(base)}&size=10")
            check("二维码接口返回 200", st == 200)
            check("返回内容为 PNG", png[:8] == b"\x89PNG\r\n\x1a\n", f"head={png[:8]!r}")
            check("PNG 体积合理 (>200 字节)", len(png) > 200, f"len={len(png)}")

            # 解码核对深链
            target = f"{base}/user/asset.html?id={aid}"
            decoded = None
            try:
                import cv2
                import numpy as np

                arr = np.frombuffer(png, dtype=np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
                det = cv2.QRCodeDetector()
                data, _, _ = det.detectAndDecode(img)
                decoded = (data or "").strip()
            except Exception as e:
                print("    [warn] 解码器不可用:", e)
            if decoded is not None:
                check("二维码可解码且内容正确", decoded == target, f"decoded={decoded!r} expected={target!r}")
            else:
                # 退回：仅确认 PNG 有效（结构上已通过前述校验）
                print(f"    [info] 无解码器，跳过内容解码；目标深链应为: {target}")

        # 不存在资产 -> 404
        st, _ = req("GET", "/api/assets/999999/qrcode")
        check("不存在资产返回 404", st == 404, f"got {st}")

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        shutil.rmtree(TMP, ignore_errors=True)

    print(f"\n结果：通过 {passed} / 失败 {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
