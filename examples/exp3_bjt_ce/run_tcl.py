# -*- coding: utf-8 -*-
import sys, os
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
dx.ensure_capture()
s = br.BRIDGE.session()
print("page:", s.eval('GetActivePage', 30))
tcl = open(sys.argv[1], encoding='utf-8-sig').read()
try:
    print(s.eval(tcl, 180))
except Exception as e:
    print("ERR:", e)
