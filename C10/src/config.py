"""全局配置：路径、预算、安全边界。

设计约束
--------
1. 所有路径由单一入口推导，禁止在业务代码里散落字符串常量。
2. 允许通过环境变量 C10_ROOT 覆盖根目录（测试隔离用）。
3. 预算（步数 / 超时 / 输出上限）是硬约束，在 L3 循环内强制执行，
   防止工具链失控或上下文爆炸。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(os.environ.get("C10_ROOT") or Path(__file__).resolve().parents[1]).resolve()

# ---- 目录 ----------------------------------------------------------------
MEM = ROOT / "memory"
K_DIR = MEM / "k"          # K: Knowledge     持久知识
S_DIR = MEM / "s"          # S: State         工作状态
T_DIR = MEM / "t"          # T: Trajectory    任务轨迹
A_DIR = MEM / "a"          # A: Archive       复盘归档（R: Reflection 沉淀于此）

SKILLS_DIR = ROOT / "skills"
PROPOSED_DIR = SKILLS_DIR / "_proposed"
LOGS = ROOT / "logs"
WORKSPACE = ROOT / "workspace"   # 工具默认可写沙箱

K_FILE = K_DIR / "knowledge.jsonl"
A_FILE = A_DIR / "lessons.jsonl"
S_FILE = S_DIR / "state.json"
INDEX_FILE = MEM / "index.json"


def trace_file(day: str) -> Path:
    """T 层按天分片，便于按时间窗回放与挖掘。"""
    return T_DIR / f"{day}.jsonl"


def ensure_dirs() -> None:
    for p in (MEM, K_DIR, S_DIR, T_DIR, A_DIR, SKILLS_DIR, LOGS, WORKSPACE):
        p.mkdir(parents=True, exist_ok=True)


# ---- 预算与安全 ----------------------------------------------------------
@dataclass(frozen=True)
class Budget:
    """单次运行的硬预算。命中任一上限即终止并按已得信息收敛输出。"""

    max_steps: int = 30            # 工具调用总步数（含技能内部步）
    tool_timeout_s: float = 20.0   # 单工具超时
    run_timeout_s: float = 180.0   # 单次任务墙钟
    max_output_chars: int = 4000   # 单步输出截断
    max_recall: int = 5            # 记忆召回条数上限


DEFAULT_BUDGET = Budget()


# ---- 安全 -----------------------------------------------------------------
# 边界策略：智能体可以改动"自己的房子"（项目根 C10/），但绝不能越出项目根。
# 读与写同一边界，换来语义一致：相对路径永远相对项目根解析，
# 不会出现"读得到、写不进"的割裂感。所有写入仍带 danger=1 进入 trace 审计。
WRITE_SANDBOX = ROOT
READ_SANDBOX = ROOT

# shell.run 的首命令白名单（最小权限原则）
SHELL_ALLOWLIST = (
    "python", "python3", "py", "pip", "git", "pytest", "node", "npm",
    "ls", "dir", "cat", "type", "echo", "find", "grep", "wc", "head", "tail",
)


# ---- LLM（可选） ----------------------------------------------------------
# 默认离线规则规划器即可跑通全链路；配置以下环境变量后自动切换为 LLM 规划器。
LLM_BASE_URL = os.environ.get("C10_LLM_BASE_URL", "")   # 例：https://api.openai.com/v1
LLM_API_KEY = os.environ.get("C10_LLM_API_KEY", "")
LLM_MODEL = os.environ.get("C10_LLM_MODEL", "gpt-4o-mini")
LLM_TIMEOUT_S = float(os.environ.get("C10_LLM_TIMEOUT_S", "30"))
