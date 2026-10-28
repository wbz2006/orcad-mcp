# -*- coding: utf-8 -*-
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br
import win32gui, win32con, win32api

TCL = r"""
set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set c [DboTclHelper_sMakeCString]; $pl GetReference $c
    set rn [DboTclHelper_sGetConstCharPtr $c]
    if { $rn == "RL" } {
        set dit [$pl NewDisplayPropsIter $st]
        set d [$dit NextProp $st]
        while { $d != $null } {
            set nm [DboTclHelper_sMakeCString]; $d GetName $nm
            set n [DboTclHelper_sGetConstCharPtr $nm]
            if { $n == "Value" } {
                set id [$d GetId $st]
                lappend out "value id=$id"
                catch { UnSelectAll }
                SelectObjectById $id
            }
            set d [$dit NextProp $st]
        }
        catch { delete_DboDisplayPropsIter $dit }
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
"""

s = None
for _ in range(20):
    try:
        s = br.BRIDGE.session(); break
    except Exception:
        time.sleep(1)
print("tcl:", s.eval(TCL, 60))
time.sleep(0.5)
print("rotate:", s.eval('Menu "Edit::Rotate"', 60))
time.sleep(1.5)
