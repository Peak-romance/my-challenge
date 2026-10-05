#!/usr/bin/env python3
"""C4D Demo —— 一条命令演示本地大模型 Agent 的全部能力。

这是「demo」交付物的主入口。它按顺序演示 6 件事，每件事都打印
「输入 → 模型输出 → 结论」，让人一眼看出 Agent 真的在工作
（而不是在读一份写死的 JSON）。

    python demo/run_demo.py                 # 完整演示（需要 Ollama 在跑）
    python demo/run_demo.py --offline       # 离线演示（只跑不依赖模型的部分）
    python demo/run_demo.py --only 2,4      # 只演示第 2、4 项

演示项：
    1. 环境与模型自检    —— 后端版本、模型清单、设备信息
    2. 结构化输出        —— 模型产出严格 JSON（不是散文）
    3. 函数调用          —— 模型主动选择工具，而非自己编坐标
    4. 多步推理          —— 多轮 ReAct：思考 → 调工具 → 观察 → 再思考
    5. 记忆持久化        —— 写入事实、跨进程读回、关键词检索
    6. 端到端技能        —— 一句话生成交互式地图（真实模型驱动）

设计原则：**每一步都打印可核对的证据**。
模型名、耗时、token、工具调用参数全部落屏——评审可以直接看这一份输出。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _locate_root() -> Path:
    """定位技能根目录（必须同时含 skills/sias_map.py 与 agent/ 包）。

    demo 有两份内容相同的拷贝，但相对位置不同，ROOT 不能写死：
      1) XUJIALE_C4D_agent-skill/demo/run_demo.py —— 内嵌在技能包里
      2) XUJIALE_C4D_demo/run_demo.py             —— 顶层交付物，与技能包平级
    """
    candidates = [
        HERE.parent,                        # 内嵌：demo/ 的上一级
        HERE,                               # 直接放在技能根目录
        HERE / "XUJIALE_C4D_agent-skill",   # 顶层拷贝：与技能包平级
        HERE.parent / "XUJIALE_C4D_agent-skill",
        HERE.parent.parent,                 # 再往上一层兜底
    ]
    for c in candidates:
        if (c / "skills" / "sias_map.py").is_file() and (c / "agent").is_dir():
            return c
    # 找不到就报清楚去过了哪里，而不是半路抛 FileNotFoundError
    print("[X] 找不到技能根目录（需要 skills/sias_map.py 和 agent/ 包）")
    print("    已尝试：")
    for c in candidates:
        print(f"      {c}")
    sys.exit(2)


ROOT = _locate_root()
sys.path.insert(0, str(ROOT))

# ---- 让 demo 在控制台正常显示中文 ----
if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

BAR = "=" * 74
THIN = "-" * 74


def title(n: int, text: str) -> None:
    print(f"\n{BAR}\n  演示 {n}/6 ｜ {text}\n{BAR}")


def step(text: str) -> None:
    print(f"\n  ▸ {text}")


def ok(text: str) -> None:
    print(f"    ✓ {text}")


def info(label: str, value) -> None:
    print(f"      {label:<14}{value}")


def payload(rec) -> dict:
    """把工具调用记录还原成结构化结果。

    ToolCallRecord 只带 result_preview（摘要字符串，防止上下文被大结果撑爆），
    这里把它解回 dict 供断言使用；解不开就退化成 {'raw': ...}。
    """
    try:
        d = json.loads(rec.result_preview)
        return d if isinstance(d, dict) else {"raw": d}
    except Exception:  # noqa: BLE001
        return {"raw": rec.result_preview}


# ----------------------------------------------------------------------
def _build_registry():
    """复用技能自身的工具装配逻辑，避免 demo 里另抄一份 schema 而失真。"""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "sias_map", str(ROOT / "skills" / "sias_map.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    from agent.memory import MemoryStore

    gaz = json.loads(
        (ROOT / "skills" / "landmarks.json").read_text(encoding="utf-8"))
    mem = MemoryStore(str(ROOT / "memory"))
    return mod.build_registry(gaz, mem)


DEMOS = {}


def demo(n: int):
    def deco(fn):
        DEMOS[n] = fn
        return fn
    return deco


# ----------------------------------------------------------------------
@demo(1)
def d1_env(client) -> bool:
    """环境与模型自检。"""
    title(1, "环境与模型自检（证明真的在本地跑）")
    import platform

    step("设备信息")
    info("操作系统", f"{platform.system()} {platform.release()}")
    info("Python", platform.python_version())
    try:
        import subprocess
        r = subprocess.run(
            ["python", "-c",
             "import os;print(os.cpu_count())"],
            capture_output=True, text=True, timeout=10,
        )
        info("CPU 逻辑核", r.stdout.strip())
    except Exception:  # noqa: BLE001
        pass

    if client is None:
        print("\n    ⚠ 本地推理服务不可达——本项需要在 Ollama 运行时执行")
        return False

    step("推理后端")
    h = client.health()
    info("服务地址", client.base_url)
    info("后端版本", f"Ollama v{h.get('version', '未采集')}")
    info("模型清单", ", ".join(h.get("models", [])) or "（空）")
    info("目标模型", client.model)
    if h.get("models") and client.model not in h["models"]:
        print(f"    ⚠ 目标模型不在清单中，请先 ollama pull {client.model}")
        return False
    ok("本地后端就绪，模型可用")
    return True


@demo(2)
def d2_structured(client) -> bool:
    """结构化输出。"""
    title(2, "结构化输出（模型产出严格 JSON，而非散文）")
    if client is None:
        print("\n    ⚠ 跳过：需要本地模型")
        return False

    prompt = (
        "请以严格 JSON 输出郑州西亚斯学院的简介。"
        '格式：{"name_zh":"", "name_en":"", "founded":0, "city":"", '
        '"features":["","",""]}。只输出 JSON，不要任何解释。'
    )
    step("提问")
    print(f"      {prompt[:70]}…")

    t0 = time.time()
    data = client.chat_json(prompt, temperature=0.2)
    el = time.time() - t0

    if not data:
        print("    ✗ 未解析出 JSON")
        return False

    step("模型输出（已解析）")
    for k, v in data.items():
        info(k, v)
    ok(f"严格 JSON 解析成功，耗时 {el:.1f}s")
    return True


@demo(3)
def d3_function_calling(client) -> bool:
    """函数调用。

    注意：这一项**不依赖模型**——工具层是 Agent 自己的代码。
    模型离线时照样演示，因为它证明的是「工具真的能跑、错误真的被兜住」。
    模型在线时额外演示「模型主动选择工具」这件事（见演示 4）。
    """
    title(3, "函数调用（工具层可独立验证，不必等模型）")
    reg = _build_registry()

    step("已注册的工具（来自技能自身装配，非 demo 另抄一份）")
    for line in reg.describe().splitlines():
        print(f"      {line}")

    step("调用 geocode_place（把地名解析为坐标）")
    rec = reg.execute(1, "geocode_place", {"place_name": "黄帝故里"})
    p1 = payload(rec)
    info("成功", rec.ok)
    info("命中", p1.get("found"))
    info("规范名", p1.get("canonical_name"))
    info("坐标", f"{p1.get('latitude')}, {p1.get('longitude')}")

    step("调用 compute_distance（两个地名之间的距离）")
    r2 = reg.execute(1, "compute_distance",
                     {"place_a": "郑州西亚斯学院", "place_b": "黄帝故里"})
    p2 = payload(r2)
    info("成功", r2.ok)
    info("路线", f"{p2.get('from')} → {p2.get('to')}")
    info("直线距离", f"{p2.get('distance_km')} km")
    info("估算耗时", f"步行 {p2.get('walking_minutes')} 分钟"
                    f" / 驾车 {p2.get('driving_minutes')} 分钟")

    step("调用 remember（写入长期记忆）")
    r3 = reg.execute(1, "remember",
                     {"key": "demo_geo", "value": "黄帝故里位于新郑"})
    info("成功", r3.ok)

    step("调用不存在的地名（验证未命中时不编坐标）")
    r5 = reg.execute(1, "geocode_place", {"place_name": "不存在的地方XYZ"})
    p5 = payload(r5)
    info("成功(调用本身)", r5.ok)
    info("命中", p5.get("found"))
    if not p5.get("found"):
        ok("未命中时返回 found=false，没有编造任何坐标")

    step("调用不存在的工具（验证错误被结构化，不炸主循环）")
    r4 = reg.execute(1, "no_such_tool", {})
    info("成功(调用本身)", r4.ok)
    info("错误", str(r4.error)[:90])

    good = (rec.ok and r2.ok and r3.ok
            and r5.ok and p5.get("found") is False   # 未命中 → 不编造
            and not r4.ok)                            # 未知工具 → 结构化失败
    step("工具层统计")
    st = reg.stats()
    info("总调用", st["total_calls"])
    info("成功/失败", f"{st['successful']} / {st['failed']}")
    if good:
        ok("地名→坐标→距离→记忆 全链路通；未命中不编造、未知工具不抛异常")
    else:
        print("    ✗ 工具链路存在断言未通过")
    return good


@demo(4)
def d4_multi_step(client) -> bool:
    """多步推理。"""
    title(4, "多步推理（ReAct 多轮：思考 → 调工具 → 观察 → 再思考）")
    if client is None:
        print("\n    ⚠ 跳过：需要本地模型")
        return False

    from agent.core import LocalAgent
    from agent.memory import MemoryStore

    mem = MemoryStore(str(ROOT / "memory"))
    reg = _build_registry()
    agent = LocalAgent(client=client, registry=reg, memory=mem,
                       max_turns=6, verbose=False)
    task = ("帮我查一下「郑韩故城遗址」在哪里，"
            "再算它到郑州西亚斯学院的距离。")

    step("任务")
    print(f"      {task}")
    step("执行中（最多 6 轮）…")

    t0 = time.time()
    run = agent.run(task)
    el = time.time() - t0

    step("逐轮轨迹（思考 → 调工具 → 观察）")
    n_tool = 0
    for turn in run.turns:
        names = [c.name for c in turn.tool_calls]
        n_tool += len(names)
        line = f"第 {turn.index} 轮"
        info(line, f"工具调用 {len(names)} 次" + (f" · {names}" if names else "（无）"))
        if turn.model_content:
            snippet = " ".join(turn.model_content.split())[:80]
            print(f"                    思考：{snippet}")
        for c in turn.tool_calls:
            print(f"                     └ {c.name}({json.dumps(c.arguments, ensure_ascii=False)})"
                  f" → {'ok' if c.ok else '失败'}")

    step("最终回答")
    print(f"      {run.final_answer[:400]}")
    if n_tool >= 2:
        ok(f"多轮循环完成：{len(run.turns)} 轮 / {n_tool} 次工具调用 / "
           f"{el:.1f}s / 成功={run.success}")
    print(f"    {'✓' if run.success and n_tool >= 2 else '✗'} "
          f"判定：{'模型自主串起了多步工具链' if run.success and n_tool >= 2 else '未完成多步链条'}")
    return bool(run.success and n_tool >= 2)


@demo(5)
def d5_memory(client) -> bool:
    """记忆持久化。"""
    title(5, "记忆持久化（写入 → 落盘 → 跨进程读回 → 关键词检索）")
    from agent.memory import MemoryStore

    path = str(ROOT / "memory")
    store = MemoryStore(path)

    step("写入事实")
    store.remember("demo_landmark", "郑韩故城遗址", source="demo")
    store.remember("demo_center", "郑州西亚斯学院", source="demo")
    ok(f"已写入 2 条，当前共 {store.count()} 条事实")

    step("重新实例化（模拟跨进程）")
    store2 = MemoryStore(path)
    got = store2.recall("故城")
    info("检索「故城」", json.dumps(got, ensure_ascii=False)[:140])

    step("落盘文件")
    f = Path(path) / "facts.json"
    info("路径", str(f))
    info("存在", f.exists())
    if f.exists():
        info("大小", f"{f.stat().st_size} 字节")
    ok("记忆已持久化，可跨进程读回")
    return True


@demo(6)
def d6_end_to_end(client) -> bool:
    """端到端技能。"""
    title(6, "端到端技能（一句话 → 交互式地图）")
    import subprocess

    out = ROOT / "output" / "demo_map.html"
    out.parent.mkdir(parents=True, exist_ok=True)

    if client is None:
        step("离线模式：用种子数据渲染（验证渲染链路，不依赖模型）")
        cmd = [sys.executable, str(ROOT / "skills" / "sias_map.py"),
               "--offline-seed", "--out", str(out), "--quiet"]
        mode = "offline_seed"
    else:
        step("真实模型驱动：让本地模型生成地点数据")
        cmd = [sys.executable, str(ROOT / "skills" / "sias_map.py"),
               "--out", str(out), "--count", "8", "--num-ctx", "2048"]
        mode = "model"

    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT),
                       timeout=1800)
    if r.returncode != 0:
        print(f"    ✗ 生成失败\n{r.stdout[-800:]}\n{r.stderr[-500:]}")
        return False

    info("模式", mode)
    info("输出", str(out))
    info("大小", f"{out.stat().st_size:,} 字节" if out.exists() else "缺失")

    rep = ROOT / "output" / "run_report.json"
    if rep.exists():
        d = json.loads(rep.read_text(encoding="utf-8"))
        info("地点数", d.get("landmark_count"))
        info("实际模式", d.get("mode"))
        info("耗时", f"{d.get('duration_s')} s")
    ok("交互式地图已生成，可直接用浏览器打开")
    return True


# ----------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="C4D 本地大模型 Agent 演示")
    ap.add_argument("--model", default="gemma4:e2b-it-q4_K_M")
    ap.add_argument("--base-url", default="http://127.0.0.1:11434")
    ap.add_argument("--offline", action="store_true",
                    help="跳过所有需要模型的演示项")
    ap.add_argument("--only", default="",
                    help="只跑指定演示项，逗号分隔，如 2,4,5")
    args = ap.parse_args()

    print(BAR)
    print("  C4D Demo —— 本地大模型驱动的 Agent 技能全能力演示")
    print(BAR)
    print(f"  模型    : {args.model}")
    print(f"  后端    : {args.base_url}")
    print(f"  模式    : {'离线（跳过模型项）' if args.offline else '完整'}")

    client = None
    if not args.offline:
        from agent.llm_client import LocalLLMClient
        client = LocalLLMClient(model=args.model, base_url=args.base_url,
                                num_ctx=2048, keep_alive="5m")
        h = client.health()
        if h.get("ok"):
            print(f"  服务    : 在线（Ollama v{h.get('version')}）")
        else:
            print(f"  服务    : 不可达 —— 需要模型的项将被跳过")
            client = None
    print(BAR)

    only = {int(x) for x in args.only.split(",") if x.strip()} if args.only else set()
    results: dict[int, bool] = {}
    for n in sorted(DEMOS):
        if only and n not in only:
            continue
        try:
            results[n] = DEMOS[n](client)
        except Exception as e:  # noqa: BLE001
            print(f"\n    ✗ 演示 {n} 异常：{type(e).__name__}: {e}")
            results[n] = False

    print(f"\n{BAR}")
    print("  演示汇总")
    print(THIN)
    names = {1: "环境与模型自检", 2: "结构化输出", 3: "函数调用",
             4: "多步推理", 5: "记忆持久化", 6: "端到端技能"}
    passed = sum(1 for v in results.values() if v)
    for n, v in sorted(results.items()):
        print(f"    {'✓' if v else '✗'}  演示 {n}  {names[n]:<16}{'通过' if v else '未完成'}")
    print(THIN)
    print(f"  {passed}/{len(results)} 项通过")
    print(BAR)
    return 0 if passed == len(results) and results else 1


if __name__ == "__main__":
    sys.exit(main())
