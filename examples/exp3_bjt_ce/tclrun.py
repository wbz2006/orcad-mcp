# -*- coding: utf-8 -*-
"""Evaluate a .tcl file in Capture without the GetActivePage pre-check."""
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE)
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br

path = sys.argv[1]
tcl = open(path, encoding="utf-8-sig").read()
s = None
for _ in range(20):
    try:
        s = br.BRIDGE.session(); break
    except Exception:
        time.sleep(1)
if s is None:
    print("no agent"); sys.exit(1)
print(s.eval(tcl, int(sys.argv[2]) if len(sys.argv) > 2 else 120))
