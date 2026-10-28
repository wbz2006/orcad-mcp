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
TCL = r'''
set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set it [$pg NewGlobalsIter $st]
set g [$it NextGlobal $st]
while { $g != $null } {
    set l [$g GetLocation $st]
    lappend out "GLOB [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"
    set g [$it NextGlobal $st]
}
catch { delete_DboPageGlobalsIter $it }
foreach pt { {100 90} {90 420} {330 489} {570 510} {630 500} {840 330} } {
    set x [lindex $pt 0]; set y [lindex $pt 1]
    set p [DboTclHelper_sMakeCPoint $x $y]
    set cc -1; catch { set cc [$pg GetConnectionCount $p $st] }
    lappend out "CONN $x,$y = $cc"
}
set n 0
set pit [$pg NewPartInstsIter $st]
set i [$pit NextPartInst $st]
while {$i != $null} { incr n; set i [$pit NextPartInst $st] }
catch {delete_DboPagePartInstsIter $pit}
set nw 0
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
while {$w != $null} { incr nw; set w [$wit NextWire $st] }
catch {delete_DboPageWiresIter $wit}
lappend out "PARTS $n WIRES $nw"
return $out
'''
print(s.eval(TCL, 120))
