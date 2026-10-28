# -*- coding: utf-8 -*-
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE); sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
dx.ensure_capture()
s = br.BRIDGE.session()

FIND = r"""
set pg [GetActivePage]
set st [DboState]
set null NULL
set target $null
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
while { $w != $null } {
    set a [$w GetStartPoint $st]; set b [$w GetEndPoint $st]
    set p1 [list [DboTclHelper_sGetCPointX $a] [DboTclHelper_sGetCPointY $a]]
    set p2 [list [DboTclHelper_sGetCPointX $b] [DboTclHelper_sGetCPointY $b]]
    if { ( $p1 == {%X1% %Y1%} && $p2 == {%X2% %Y2%} ) || ( $p1 == {%X2% %Y2%} && $p2 == {%X1% %Y1%} ) } { set target $w }
    set w [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
if { $target == $null } { return "notfound" }
catch { UnSelectAll }
SelectObjectById [$target GetId $st]
return "selected"
"""

COUNT = r"""
set pg [GetActivePage]
set st [DboState]
set null NULL
set n 0
set it [$pg NewWiresIter $st]; set w [$it NextWire $st]
while { $w != $null } { incr n; set w [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
return $n
"""

segs = [(550,240,550,190),(550,280,550,320),(550,320,440,320),(550,320,620,320),(620,320,620,230),(650,230,840,230),(840,230,840,290)]
for (x1,y1,x2,y2) in segs:
    t = FIND.replace("%X1%",str(x1)).replace("%Y1%",str(y1)).replace("%X2%",str(x2)).replace("%Y2%",str(y2))
    r = s.eval(t, 60)
    if "selected" not in str(r):
        print(f"{x1},{y1}-{x2},{y2}: {r}")
        continue
    m = s.eval('Menu "Edit::Delete"', 60)
    print(f"del {x1},{y1}-{x2},{y2} -> menu={m} count={s.eval(COUNT,60)}")
    time.sleep(1.0)
time.sleep(3)
print("final wires:", s.eval(COUNT, 60))

