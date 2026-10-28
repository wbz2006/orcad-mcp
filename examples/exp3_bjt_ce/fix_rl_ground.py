# -*- coding: utf-8 -*-
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br
import draw_exp3 as dx
dx.ensure_capture()
s = br.BRIDGE.session()

TCL = r'''
set pg [GetActivePage]
set st [DboState]
set null NULL
set done 0
set it [$pg NewGlobalsIter $st]
set g [$it NextGlobal $st]
while { $g != $null } {
    set l [$g GetLocation $st]
    set x [DboTclHelper_sGetCPointX $l]
    set y [DboTclHelper_sGetCPointY $l]
    if { $x == 840 && $y == 290 } {
        set np [DboTclHelper_sMakeCPoint 840 330]
        set r [$g SetLocation $np]
        set done 1
    }
    set g [$it NextGlobal $st]
}
catch { delete_DboPageGlobalsIter $it }
return $done
'''
print("moved:", s.eval(TCL, 60))

# verify
TCL2 = r'''
set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set it [$pg NewGlobalsIter $st]
set g [$it NextGlobal $st]
while { $g != $null } {
    set l [$g GetLocation $st]
    lappend out "[DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"
    set g [$it NextGlobal $st]
}
catch { delete_DboPageGlobalsIter $it }
return $out
'''
print("globals:", s.eval(TCL2, 60))

# save
s.eval('SelectPMItem {SCHEMATIC1}', 60)
time.sleep(1)
try:
    print("save:", s.eval('Menu "File::Save"', 60))
except Exception as e:
    print("save err:", e)
time.sleep(3)
print("saved")
