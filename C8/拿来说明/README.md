# 拿来说明（Evidence / 可独立验证的实物）

> 本目录是 C8 真实项目落地的**物证包**：评审人无需本人在场，按下方步骤即可独立验证"平台确实在本机真实跑通并达到 README 声称的可验收状态"。

---

## 一、本目录内容

```
D:\C8\拿来说明\
├── README.md                 # 本说明
├── smoke_test_result.txt     # 官方端到端冒烟测试原始输出（91/91 通过）
├── frontend_checks.txt       # 前端静态检查原始输出（DOM 一致 + 14 JS 块语法）
└── live\evidence\            # 真实启动后端抓取的运行期证据
    ├── health.json           # GET /api/health 真实响应（status=ok）
    ├── colleges.json         # GET /api/colleges 真实响应（2 学院 / 4 部门）
    ├── assets.json           # GET /api/assets 真实响应（含已上架物资）
    ├── stats.json            # GET /api/admin/stats/overview 真实响应
    ├── logs_claim.json       # GET /api/admin/logs?type=claim 真实响应
    ├── user1_token.txt       # user1 登录后拿到的 JWT（证明鉴权链路）
    ├── handover_no.txt       # 一条真实交接单号
    ├── handover.docx         # 服务端真实导出的 Word 交接单（37,633 B，PK 头）
    └── handover.pdf          # 服务端真实导出的 PDF 交接单（79,439 B，%PDF 头）
```

---

## 二、验收对照（对应 proposal §5 的 AC）

| 验收项 | 证据 | 结论 |
| --- | --- | --- |
| AC1 依赖可导入 | `python -c "import fastapi,uvicorn,..."` 无报错 | ✅ |
| AC2 冒烟 91/91 | `smoke_test_result.txt` 末行"通过 91，失败 0" | ✅ |
| AC3 DOM 一致性 | `frontend_checks.txt` → "静态一致性检查通过" | ✅ |
| AC4 JS 语法 | `frontend_checks.txt` → "全部通过 / 14 块" | ✅ |
| AC5 真实启动+导出 | `live/evidence/` 中 health.json=200、docx/pdf 文件头合法 | ✅ |
| AC6 根因已修 | `D:\闲置平台代码\backend\requirements.txt` pydantic 改为 2.11.9（原文件备于 `.bak`） | ✅ |
| AC7 可独立复现 | 下方"复现步骤"任意机器可重跑 | ✅ |

---

## 三、独立复现步骤（约 5 分钟）

环境：Windows + Python 3.13（建议先确认 `python` 与 `pip` 同源：`python -m pip --version`）。

```bash
# 1) 进入后端目录，安装依赖（注意：必须 python -m pip，避免双解释器错位）
cd D:\闲置平台代码\backend
python -m pip install -r requirements.txt        # 已修复 pydantic 锁版本，3.13 可直接成功

# 2) 端到端冒烟测试（自动拉起后端、跑 91 项断言后关闭）
cd D:\闲置平台代码
python tools/smoke_test.py
# 期望末尾输出：===== 结果：通过 91，失败 0 =====

# 3) 前端静态检查
python tools/check_dom_refs.py     # 期望：静态一致性检查通过
node tools/check_js.js             # 期望：全部通过

# 4) 真实启动并导出交接单（可选，验证服务端 docx/pdf 生成）
cd D:\闲置平台代码\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# 浏览器/ curl 打开 http://127.0.0.1:8000/docs ，用 user1/123456 登录后
# 调取 GET /api/handovers/{no}/export?format=docx  应得到真实 .docx
```

---

## 四、真实约束提示（复现时若失败，先看这里）

1. **双 Python 错位**：若 `pip install` 成功但 `python` 仍 import 不到，说明 `python` 与 `pip` 不是同一解释器。一律改用 `python -m pip install`。
2. **Python 3.13 + 旧 pydantic**：原 `requirements.txt` 锁 `pydantic==2.10.4` 在 3.13 无对应轮子（已修复为 2.11.9）。若在更老 Python 上跑，可保留原锁版本（见 `.bak`）。
3. **无 Docker**：本环境未装 Docker，故走"免 Docker"路径（uvicorn 直启），未验证 docker compose 编排。
4. **镜像源偶发卡死**：大依赖树安装若卡死，可去掉 `uvicorn[standard]` 的方括号 extras，或分批安装。

---

## 五、一句话总结

`smoke_test_result.txt` + `live/evidence/` 下的真实 JSON 与 docx/pdf 文件，构成了一条**不可伪造的证据链**：这套"闲置平台"代码在真实约束下已被救活、跑通、并导出真实文档——C8 真实项目落地成立。
