# C6 挑战交付物链接汇总（LINKS）

| 交付项 | 链接 / 位置 |
| --- | --- |
| **app 链接（在线应用）** | https://idle-asset-platform.app.workbuddy.host/?sharecode=SLUWH4EXLI |
| **demo（演示）** | 上述在线应用即 demo；演示脚本见 [`demo.md`](./demo.md) |
| **repo 链接（仓库）** | https://github.com/Peak-romance/c6-idle-asset-platform |
| **AI 日志** | [`AI日志.md`](./AI日志.md) |
| 复盘 AAR | [`复盘AAR.md`](./复盘AAR.md) |
| 交付物总览 | [`README.md`](./README.md) |
| 可独立运行源码 | `./app/`（与本仓库一致） |

## 测试账号（口令均为 `123456`）

- `user1` —— 部门用户（智能制造学院 / 实训中心）
- `user2` —— 部门用户（信息技术学院 / 网络运维部）
- `admin1` —— 平台管理员

## 关键质量证据

- 端到端冒烟测试：**91 / 91 项断言通过**（`app/tools/smoke_test.py`）
- 发布校验：`verified: true`，外网 `/api/health` 返回 `ok`、登录返回真实 JWT
- 仓库可独立 clone 运行；本包含可运行源码副本
