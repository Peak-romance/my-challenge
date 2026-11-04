# C9 自驱项目 AI 使用日志（AI Usage Log）

> 交付物位置：`D:\C9\AI日志\AI日志.md`
> 说明：本项目使用 **WorkBuddy（AI 助手）** 作为唯一 AI 工具，独立完成选题、代码勘察、实现、验证与文档撰写。本日志记录每一阶段"用 AI 做了什么、怎么用、产出如何被客观校验"，确保 AI 使用**恰当、有效、可追溯**（对应评分 aiUsage 20 分）。

---

## 使用总览

| 维度 | 情况 |
| --- | --- |
| AI 工具 | WorkBuddy（对话式 AI + 工具调用：Bash / Read / Edit / Write / AskUserQuestion） |
| 用途 | 代码勘察、选题对齐、独立产物搭建、后端/前端实现、端到端验证脚本、三份交付物撰写 |
| 是否替代人决策 | 否。选题方向经用户拍板；所有修复由 AI 提出方案并经客观测试验证后采纳 |
| 可追溯性 | 每一步均有命令、文件路径、测试输出可查（见 `artifact/tools/verify_qr.py` 与过程日志） |

---

## 阶段化日志

### [T0] 选题对齐（11-03）
- **AI 动作**：用 `AskUserQuestion` 给出 3 个自驱方向——批量导入真实库存 / 一键部署交付包 / 交互增强(二维码扫码认领)。
- **提示词策略**：把"选题价值必须真实"作为硬约束，选项均指明"可独立运行、可演示"。
- **用户决策**：选 **交互增强——资产二维码与扫码认领**。
- **产出**：定调，避免自驱选题的主观发散。
- **校验**：用户明确选择，方向收敛。

### [T1] 代码勘察（11-03）
- **AI 动作**：`ls`/`find` 探查 `D:\闲置平台代码` 与 `D:\闲置平台`（真实库存 Excel）；读取 `README.md`、`backend/app/models.py`、`routers/assets.py`、`deps.py`、`main.py`、`config.py`、`frontend/js/{api,common}.js`、`user/asset.html`、`admin/assets.html`。
- **关键判断**：确认平台业务模型成熟、资产表字段与真实库存高度契合；QR 接口应设为**公开**以避免 `<img src>` 鉴权问题。
- **校验**：所有约定与代码一致，无矛盾。

### [T2] 独立产物搭建（11-03 → 11-04）
- **AI 动作**：`tar` 复制 `D:\闲置平台代码` → `D:\C9\artifact`，排除 `.venv / __pycache__ / database/data / backend/data / logs / .env`。
- **结果**：产物 3.9M 干净副本，原代码零改动。
- **校验**：`ls` 确认文件齐全，`du -sh` 确认体积。

### [T3] 后端实现（11-04）
- **AI 动作**：
  - `Write` 新建 `backend/app/routers/qrcode.py`：公开接口 `GET /api/assets/{id}/qrcode`，用 `segno` 生成 PNG，编码深链；`base` 缺省取 `request.base_url`，支持跨设备扫码。
  - `Edit` 在 `main.py` 注册路由；`Edit` 在 `requirements.txt` 加 `segno==1.6.1`。
- **首轮失败**：`python -c "import app.main"` 报 `NameError: name 'Depends' is not defined`。
- **修复**：补 `from fastapi import APIRouter, Depends, Query, Request`，重跑 import OK。
- **校验**：import 通过；逻辑上接口免鉴权、内容仅含深链。

### [T4] 前端实现（11-04）
- **AI 动作**：
  - `Edit` `frontend/js/api.js`：加 `qrcodeUrl(assetId, base, size)`。
  - `Edit` `frontend/js/common.js`：在 `ADMIN_LINKS` 加 `{key:"labels", label:"资产标签", href:"/admin/labels.html"}`。
  - `Edit` `frontend/user/asset.html`：加「二维码」按钮 + `bindQr`/`showQr`（弹窗查看/下载）。
  - `Write` 新建 `frontend/admin/labels.html`：勾选物资→批量生成二维码标签→A4 打印（含名称+编号+剩余，打印样式独立于 Tailwind）。
  - `Edit` `README.md`：补功能表项与公开接口安全说明。
- **校验（代码级）**：逐一 `grep` 确认所调用的 `API.adminListAssets`、`PAIP.statusBadge`、`PAIP.escapeHtml`、`PAIP.openModal`、`PAIP.boot`、`deps.asset_dict` 字段（`id/asset_no/name/location/manage_dept/remaining_count/unit/status`）均真实存在，无断链。

### [T5] 端到端验证（11-04）★耗时主要在"契约误判"
- **AI 动作**：`Write` `tools/verify_qr.py`——启动后端（临时 DB，自动种子）→ 登录 → 取资产 id → 调二维码接口 → opencv 解码核对 → 测 404。
- **四连返工（全部是"对既有契约的假设错"，非功能错）**：
  1. 误以为 `/api/assets` 公开 → 实际 401 需登录 → 改用 `/api/admin/assets` + token。
  2. 假设登录字段 `access_token` → 实际为 `token`。
  3. 假设 `req()` 返回已解析 JSON → 实际返回 `bytes` → 补 `json.loads`。
  4. 解码块引用了已删除的 `np_from_bytes` → 改为 `np.frombuffer`。
- **每轮均读源码取证**：`auth.py`（确认 `token`）、`routers/assets.py`+`deps.asset_dict`（确认列表结构与字段名）、`config.py`（确认 env 覆盖优先级），把假设变确认。
- **最终结果**：`python tools/verify_qr.py` → **通过 8，失败 0**，含 opencv 真实解码出 `http://192.168.1.50:3000/user/asset.html?id=4`。
- **校验**：脚本输出落盘可读；解码内容与目标深链完全一致。

### [T6] 产物清理（11-04）
- **AI 动作**：删除验证用的 `.venv`（81M，含本机绝对路径，不应随交付物发布；`start.sh` 首次运行会自建）；删除 `tools/_runtime_*` 与占位 `database/data`；校验 `database/data/uploads` 仅为空占位（`.gitignore` 已忽略）。
- **结果**：artifact 清洁 **2.1M**。
- **校验**：`du -sh`、`ls` 确认无 venv/运行时数据。

### [T7] 交付物撰写（11-04）
- **AI 动作**：撰写 `proposal/proposal.md`、`AAR_W/AAR_W.md`、`AI日志/AI日志.md`，对齐 C8 文档深度与命名规范。
- **策略**：proposal 定义选题价值与 8 项可量化 AC；AAR 深度复盘自驱动力与阻力；日志强调可追溯。
- **校验**：三份文档均落盘，目录结构符合 `D:\C9\{proposal, AAR_W, AI日志, artifact\}`。

---

## AI 使用评价（自我复盘）

- **恰当性**：AI 承担"代码侦探 + 实现 + 验证脚本 + 文档生成"，未替用户做业务价值判断（选题经用户拍板）；安全权衡（公开接口最小暴露）由 AI 提出并经人工审阅。
- **有效性**：5 处返工（1 后端 + 4 验证）全部由 AI 从报错/源码中定位根因并迭代，最终验证 8/8 全过——AI 在"从失败到修复"的闭环中价值最大。
- **可追溯性**：每个阶段都有命令、文件路径、测试输出；关键证据（`verify_qr.py` 8/8 输出、解码实证）可重跑。
- **改进点**：若在 T3 动手前就让 AI 先生成"既有契约清单"（复用 API 名/字段/函数/鉴权），可省掉 T5 的四连返工。这已写入 AAR §6 改进方案 1。

---

## 关键产物索引（均在 D:\C9\）

| 产物 | 路径 |
| --- | --- |
| 提案 | `proposal/proposal.md` |
| 复盘 | `AAR_W/AAR_W.md` |
| AI 日志 | `AI日志/AI日志.md` |
| 可运行产物 | `artifact\`（复制平台 + 二维码功能） |
| 验证脚本 | `artifact/tools/verify_qr.py` |
| 验证结果 | 运行脚本输出：8/8 通过（含二维码真实解码） |
| 新增后端 | `artifact/backend/app/routers/qrcode.py` |
| 新增前端 | `artifact/frontend/admin/labels.html` |
