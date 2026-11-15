#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""C10 · 第二大脑（Second Brain）— 长期智能体入口。

    python agent.py "生成今日简报"
    python agent.py --demo
    python agent.py --stats
    python agent.py --mine
    python agent.py --serve 8765

零第三方依赖，Python 3.10+。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.interfaces.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
