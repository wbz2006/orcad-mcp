# -*- coding: utf-8 -*-
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
dx.ensure_capture()
s = br.BRIDGE.session()
print("agent ok")
try:
    print(s.eval(r'Open {D:\Users\Download\exp3_BJT_CE\exp3.opj}', 300))
except Exception as e:
    print("open err:", e)
time.sleep(5)
print("done")
