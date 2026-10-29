# -*- coding: utf-8 -*-
"""把某页所有 placed inst 的 Reference 重新写一遍(触发显示属性同步), 并打印显示属性。"""
import sys
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp\examples\exp4_mos")
import exp4_common as C
import bridge as br, time

TPL = r'''
set st [DboState]
set out {}
OPage {SCHEMATIC1} {__PAGE__}
set pg [GetActivePage]
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set ref [DboTclHelper_sMakeCString]
    catch { $pl GetReferenceDesignator $ref }
    set r [DboTclHelper_sGetConstCharPtr $ref]
    set rc [catch { $pl SetEffectivePropStringValue [orCStr Reference] [orCStr $r] } e]
    lappend out "ref=$r rewrite rc=$rc"
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
$pg MarkModified
lappend out "save=[catch { Menu {File::Save} } es]"
return $out
'''

if __name__ == "__main__":
    page = sys.argv[1]
    tcl = C.SETUP_TCL + TPL.replace("__PAGE__", page)
    br.BRIDGE.ensure()
    for _ in range(30):
        if br.BRIDGE.all_sessions():
            break
        time.sleep(1)
    print(C.cap(tcl, 90))
