"""Install/uninstall the MCP agent into OrCAD Capture's capAutoLoad folder.

用法:
    python install_agent.py            # 安装(复制 agent 到 capAutoLoad)
    python install_agent.py --uninstall  # 卸载
    python install_agent.py --status   # 查看安装状态

默认 OrCAD 目录: C:\\OrCAD\\OrCAD_16.6_Lite,可用环境变量 ORCAD_DIR 覆盖。

原理: Capture 启动时自动 source capAutoLoad 下所有 *.tcl
(官方文档《OrCAD Capture Tcl/Tk Extensions》1.3.1 节)。
若安装目录不可写,可改为用户级加载: 在 %HOME%\\cdssetup\\capture\\capinit.tcl 中加一行
    source {D:/Main_FIles/free-deng/orcad-mcp/agent/orcad_mcp_agent.tcl}
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

AGENT_NAME = "orcad_mcp_agent.tcl"
PROJECT_AGENT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent", AGENT_NAME)


def orcad_root() -> str:
    return os.environ.get("ORCAD_DIR", r"C:\OrCAD\OrCAD_16.6_Lite")


def autoload_dir() -> str:
    return os.path.join(orcad_root(), "tools", "capture", "tclscripts", "capAutoLoad")


def target() -> str:
    return os.path.join(autoload_dir(), AGENT_NAME)


def main() -> int:
    ap = argparse.ArgumentParser(description="Install MCP agent into OrCAD Capture")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    dst = target()
    if args.status:
        print(("installed: " if os.path.exists(dst) else "NOT installed: ") + dst)
        return 0

    if args.uninstall:
        if os.path.exists(dst):
            os.remove(dst)
            print(f"removed {dst}")
            return 0
        print("not installed, nothing to do")
        return 0

    if not os.path.exists(PROJECT_AGENT):
        print(f"agent source missing: {PROJECT_AGENT}", file=sys.stderr)
        return 1
    if not os.path.isdir(autoload_dir()):
        print(f"capAutoLoad not found: {autoload_dir()}\n"
              "set ORCAD_DIR if your OrCAD is elsewhere.", file=sys.stderr)
        return 1
    shutil.copy2(PROJECT_AGENT, dst)
    print(f"installed {dst}")
    print("restart OrCAD Capture (or use com_launch_capture) to activate the agent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
