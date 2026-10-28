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
print("del:", s.eval('Menu "Edit::Delete"', 60))
time.sleep(1.5)
COUNT = r"""
set pg [GetActivePage]
set st [DboState]
set n 0
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
while { $i != NULL } { incr n; set i [$it NextPartInst $st] }
catch { delete_DboPagePartInstsIter $it }
return $n
"""
print("parts:", s.eval(COUNT, 60))
