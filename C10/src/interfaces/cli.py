"""L1 接口层 · 命令行。

接口层的唯一职责：把外部输入规范化为一次 run() 调用，再把结果格式化回去。
它不做规划、不碰记忆、不写文件——这样换一个接口（HTTP / 定时器 / IM 机器人）
不需要改任何下层代码，这就是分层的收益。
"""

from __future__ import annotations

import argparse
import json
import sys

from .. import config
from ..core import miner
from ..core.loop import Agent
from ..memory.kstar import KStar

BANNER = """C10 · 第二大脑（Second Brain）— 五层长期智能体
输入任务开始，`exit` 退出，`?` 查看命令
"""

HELP = """命令
  <任意文本>          交给智能体执行
  /skills             列出技能
  /tools              列出工具
  /stats              记忆分层统计
  /state              查看 S 层工作状态
  exit | quit         退出
"""


def _fix_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _print_json(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_serve(port: int) -> int:
    from .http_api import serve

    serve(port)
    return 0


def demo(agent: Agent) -> int:
    """端到端演示：一条命令走完五层 + KSTAR 四条写入路径。"""
    tasks = [
        "记住：C10 采用五层架构，记忆层用 KSTAR 四层分别承载知识/状态/轨迹/归档",
        "记录一下 C10 的进化路径是：每次运行落 T 层轨迹，定期挖掘重复序列抽成技能",
        "生成今日简报",
        "记住：写权限边界是项目根，越界一律拒绝；记个待办：验证遗忘阈值从 0.15 调到 0.2 的影响",
        "现在状态如何",
        "复盘这周",
        "自检一下系统状态",
    ]
    print("=" * 64)
    print("DEMO：五层贯通 + KSTAR 四层写入")
    print("=" * 64)
    for t in tasks:
        print()
        agent.run(t, source="demo")
    print("\n[stats]", json.dumps(agent.memory.stats(), ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    _fix_console()
    p = argparse.ArgumentParser(
        prog="agent.py",
        description="C10 第二大脑 · 五层长期智能体",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n  python agent.py \"生成今日简报\"\n  python agent.py --demo\n  python agent.py --stats\n  python agent.py --mine",
    )
    p.add_argument("task", nargs="*", help="任务文本（省略则进入交互模式）")
    p.add_argument("-t", "--task-text", dest="task_text", default="")
    p.add_argument("-s", "--session", default="default")
    p.add_argument("--json", action="store_true", help="以 JSON 输出运行结果")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--danger", action="store_true", help="允许执行级工具（shell.run）")
    p.add_argument("--stats", action="store_true")
    p.add_argument("--state", action="store_true")
    p.add_argument("--tools", action="store_true")
    p.add_argument("--skills", action="store_true")
    p.add_argument("--consolidate", action="store_true", help="记忆巩固：衰减 + 归档")
    p.add_argument("--mine", action="store_true", help="从轨迹挖掘技能草案")
    p.add_argument("--promote", metavar="NAME", help="把草案技能提升为正式技能")
    p.add_argument("--remember", metavar="TEXT", help="直接写入 K 层")
    p.add_argument("--tags", default="cli")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--serve", nargs="?", const=8765, type=int, metavar="PORT")
    args = p.parse_args(argv)

    if args.serve:
        return cmd_serve(args.serve)

    memory = KStar()
    agent = Agent(memory=memory, verbose=not args.quiet)

    if args.remember:
        rec = memory.remember(args.remember, tags=args.tags, source="cli")
        print(f"[K] 已写入 {rec['id']}（weight={rec['importance']}）{'· 去重命中' if rec.get('_dedup') else ''}")
        return 0

    if args.stats:
        _print_json(memory.stats())
        return 0

    if args.state:
        _print_json(memory.state())
        return 0

    if args.tools:
        for spec in agent.tools.specs():
            print(f"{spec['name']:<20} danger={spec['danger']}  {spec['description']}")
        return 0

    if args.skills:
        for spec in agent.skills.all():
            flag = f"  ⚠ {agent.skills.problems.get(spec.name)}" if spec.name in agent.skills.problems else ""
            print(f"{spec.name:<18} v{spec.version:<8} {spec.description}{flag}")
            print(f"{'':<18} triggers: {', '.join(spec.triggers[:6])}")
        for w in agent.skills.warnings:
            print(f"[warn] {w}")
        return 0

    if args.consolidate:
        print("[consolidate]", json.dumps(memory.decay(), ensure_ascii=False))
        return 0

    if args.mine:
        report = miner.mine(memory)
        _print_json({k: v for k, v in report.items() if k != "written"})
        print(f"[mine] 草案目录: {len(report['written'])} 个 → skills/_proposed/")
        print(f"[mine] 报告: {config.LOGS / 'mining-report.md'}")
        return 0

    if args.promote:
        try:
            dst = miner.promote(args.promote)
            print(f"[promote] 已上线: {dst}")
        except Exception as e:
            print(f"[promote] 失败: {type(e).__name__}: {e}")
            return 1
        return 0

    if args.demo:
        return demo(agent)

    task = args.task_text or " ".join(args.task).strip()
    if task:
        result = agent.run(task, source="cli", session=args.session, allow_danger=args.danger)
        if args.json:
            _print_json(result.to_dict())
        else:
            print(result.output)
        return 0 if result.ok else 2

    # ---------------- 交互模式 ----------------
    print(BANNER)
    while True:
        try:
            line = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in ("exit", "quit", ":q"):
            break
        if line in ("?", "/help"):
            print(HELP)
            continue
        if line in ("/skills", "/tools", "/stats", "/state"):
            argv2 = {"/skills": ["--skills"], "/tools": ["--tools"],
                     "/stats": ["--stats"], "/state": ["--state"]}[line]
            main(argv2)
            continue
        try:
            res = agent.run(line, source="repl", session=args.session, allow_danger=args.danger)
            print(res.output)
        except Exception as e:
            print(f"[error] {type(e).__name__}: {e}")
    return 0
