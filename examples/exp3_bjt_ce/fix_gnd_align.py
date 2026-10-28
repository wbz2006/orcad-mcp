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
set out {}
set it [$pg NewGlobalsIter $st]
set g [$it NextGlobal $st]
while { $g != $null } {
    set l [$g GetLocation $st]
    set x [DboTclHelper_sGetCPointX $l]
    set y [DboTclHelper_sGetCPointY $l]
    set nx [expr {$x - 10}]
    set np [DboTclHelper_sMakeCPoint $nx $y]
    $g SetLocation $np
    lappend out "$x,$y->$nx,$y"
    set g [$it NextGlobal $st]
}
catch { delete_DboPageGlobalsIter $it }
return $out
'''
print(s.eval(TCL, 60))
s.eval('SelectPMItem {SCHEMATIC1}', 60)
time.sleep(1)
print("save:", s.eval('Menu "File::Save"', 60))
time.sleep(2)
