# -*- coding: utf-8 -*-
"""启动 bridge 并等待 Capture agent 连上(不启动新 Capture)。"""
import sys, os, time
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br

br.BRIDGE.ensure()
for i in range(45):
    ss = br.BRIDGE.all_sessions()
    if ss:
        print("connected:", [(p, s.alive) for p, s in ss])
        break
    time.sleep(1)
else:
    print("no agent after 45s")
