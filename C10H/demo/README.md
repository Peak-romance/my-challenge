# C10H · Demo：可复现的安装验收

> 位置：`D:\C10H\demo\`
> 定位：**不依赖大模型的验收演示**。用确定性命令证明"装对了、配对、扩得动"，
> 而不是靠截图和口头描述。

---

## 1. 为什么这样设计 demo

通常的 Agent demo 是"问一句、答一句"。本次受两个真实约束限制：

1. **用户选择暂不接入模型**（不提供 API Key），所以任何"对话式演示"都只能是伪演示；
2. 截图无法证伪——它可以被摆拍，也不能被第三方重跑。

反过来想：这个 Challenge 真正要证明的是什么？是**安装正确、配置到位、扩展可用**。
这三件事**根本不需要模型**——它们全是确定性的。于是把 demo 做成验收脚本：
每条断言对应一个真实命令，跑完给出 PASS/FAIL 和证据串，第三方可以原地重跑。

**代价**：无法展示"Agent 帮我干活"的观感。
**收益**：每一条结论都可证伪、可复现、可审计。

---

## 2. 三个文件

| 文件 | 作用 | 是否需模型 |
| --- | --- | --- |
| `hermes-env.ps1` | 环境包装器：UTF-8 控制台、PATH 前置、镜像变量、便捷函数 | 否 |
| `c10h-verify.ps1` | 14 项验收断言，输出报告到 `outputs\` | 否 |
| `outputs\report-*.md/.json` | 每次运行的报告快照（带时间戳，不覆盖） | — |

---

## 3. 运行

```powershell
# 方式一：直接跑验收（脚本内部已做编码处理）
powershell -NoProfile -ExecutionPolicy Bypass -File D:\C10H\demo\c10h-verify.ps1

# 方式二：先进环境，再跑（推荐，后续可继续手敲 hermes 命令）
. D:\C10H\demo\hermes-env.ps1
& D:\C10H\demo\c10h-verify.ps1
```

退出码：`0` 全部通过 / `1` 存在失败项。适合挂 CI 或作为交付闸门。

---

## 4. 本次实测输出（2026-11-15 15:47:11）

```
═══ Hermes Agent 安装验收 · C10H ═══
主机: LAPTOP-E3H2M9C6  时间: 2026-11-15 15:47:11
  [PASS] A1   hermes.exe 已发布
  [PASS] A2   版本号 = v0.23.1
  [PASS] A3   代码检出 = 锁定提交      └─ HEAD=3b421578588243f920886e6fe79a6faa87ea026e
  [PASS] A4   运行时 Python 3.14.9
  [PASS] A5   工具库 9 件套齐备        └─ 10/10 命中: git-2.56.1+1, uv-0.13.5, python-3.14.9,
                                          node-26.12.1, npm-12.0.2, pnpm-12.15.0, ripgrep-15.2.0,
                                          ffmpeg-9.0.1, chromium-1208, cua-driver-0.21.0
  [PASS] A6   config.yaml 存在且版本正确 └─ _config_version=53
  [PASS] A7   USER.md 画像已写入        └─ 1001 chars  锚点命中=True
  [PASS] A8   MEMORY.md 环境事实已写入  └─ 1393 chars  锚点命中=True
  [PASS] A9   SOUL.md 已本机定制
  [PASS] A10  自定义技能已注册          └─ skills list 命中 c10h-delivery-audit (local/enabled)
  [PASS] A11  定时任务已创建            └─ job=de7e53f5db3b  每日09:00 Asia/Shanghai  no-agent
  [PASS] A12  审计脚本可独立运行        └─ | C10H | 6/6 | 29 | 0.19 | — |
  [PASS] A13  .env 无明文密钥泄漏       └─ 已赋值变量 11 个，无明文密钥
  [PASS] A14  doctor 关键检查项通过     └─ security=True  python=True  config=True

═══ 结果: 14/14 通过, 0 失败 ═══
```

> 完整报告：`outputs\report-20261115-154711.md`（同目录下还保留了 3 份更早的运行快照，可对比迭代过程）。


> A14 说明：`doctor` 因本机 `schtasks.exe` 被安全策略拦截而无法完整跑完，
> 故断言只取前序三段（安全公告 / Python 环境 / 配置文件）。这是**弱化后的断言**，
> 不做"doctor 全绿"的虚假陈述。

---

## 5. 五步演示剧本（约 5 分钟）

| 步 | 命令 | 看点 |
| --- | --- | --- |
| 1 | `. D:\C10H\demo\hermes-env.ps1` | 环境就绪：UTF-8 + PATH + 镜像，一行解决三个坑 |
| 2 | `hermes --version` | v0.23.1 / Python 3.14.9 / "Up to date" |
| 3 | `hermes skills list \| Select-String c10h` | 自定义技能确实是 `local / enabled` |
| 4 | `hermes cron list` | 每日 09:00 巡检任务，`no-agent` 模式 |
| 5 | `Invoke-DeliveryAudit` 或 `python ...\audit.py --root D:\` | 真实扫描 D 盘 8 个编号目录，输出完整度表 |

第 5 步是本 demo 的落点：**这个能力不依赖模型**，直接跑脚本就有结论；
接上模型后，同一能力也能由 Agent 自行调度。

---

## 6. 个性化扩展：`c10h-delivery-audit`

为解决"每次 Challenge 交付前不确定是否交齐"这个真实痛点而做。

```powershell
python "%LOCALAPPDATA%\hermes\skills\c10h-delivery-audit\scripts\audit.py" --root "D:\"
```

输出（节选，本交付完成前的快照）：

```
| 编号 | 完整度 | 文件数 | 体积(MB) | 缺失项 |
| C9   | 5/6 | 62 | 1.92 | 安装记录 |
| C10  | 4/6 | 61 | 0.38 | 方案/提案、安装记录 |
| C10H | 2/6 | 14 | 0.13 | 方案/提案、配置说明、AI日志、复盘AAR |
```

它同时是这个交付包的**自检工具**：本包完成后重跑，C10H 应当从 2/6 变为 6/6。
这个"用自己造的工具审自己"的闭环，比任何自述都更有说服力。

---

## 7. 边界与未验证项（诚实声明）

| 项 | 状态 | 说明 |
| --- | --- | --- |
| 多轮对话 / 工具调用 | **未验证** | 无模型，无法产生推理 |
| 跨会话记忆召回 | **未验证** | 记忆文件已就位，但"下个会话还认得你"需要模型才能演示 |
| 消息平台接入（微信/Telegram） | 未配置 | 需用户本人扫码授权，AI 不代填 |
| `doctor` 完整通过 | 受限 | `schtasks` 被黑名单拦截，前序检查项已通过 |
| cron 自动触发 | 未验证 | 缺 gateway 进程；手动 `cron run` 已成功执行 |

接入模型后，建议按此顺序补验：`hermes -z "复述 USER.md 第一条"`（记忆）→
`hermes -z "用 audit.py 审一下 D 盘"`（工具调度）→ 重启会话再问一次（跨会话记忆）。
