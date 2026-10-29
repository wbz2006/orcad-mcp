# -*- coding: utf-8 -*-
"""列出/修正某页已放置元件的位号。用法:
    python fix_refs.py PAGE1            # 只列出
    python fix_refs.py PAGE1 V1=3V V2=5V  # 按 Value 匹配设置位号
"""
import sys
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp\examples\exp4_mos")
import exp4_common as C

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
    set val [DboTclHelper_sMakeCString]
    catch { $pl GetPartValue $val }
    set l [$pl GetLocation $st]
    lappend out "ref=[DboTclHelper_sGetConstCharPtr $ref] val=[DboTclHelper_sGetConstCharPtr $val] x=[DboTclHelper_sGetCPointX $l] y=[DboTclHelper_sGetCPointY $l]"
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
__SETS__
$pg MarkModified
lappend out "save=[catch { Menu {File::Save} } es]"
return $out
'''

SET_TPL = r'''
set it2 [$pg NewPartInstsIter $st]
set j [$it2 NextPartInst $st]
while { $j != $null } {
    set pl [DboPartInstToDboPlacedInst $j]
    set val [DboTclHelper_sMakeCString]
    catch { $pl GetPartValue $val }
    if { [string equal [DboTclHelper_sGetConstCharPtr $val] "__VAL__"] } {
        set rc [catch { $pl SetEffectivePropStringValue [orCStr Reference] [orCStr __REF__] } e]
        lappend out "set __VAL__ -> __REF__ rc=$rc"
    }
    set j [$it2 NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it2 }
'''

if __name__ == "__main__":
    page = sys.argv[1]
    sets = ""
    for arg in sys.argv[2:]:
        ref, val = arg.split("=", 1)
        sets += SET_TPL.replace("__REF__", ref).replace("__VAL__", val)
    tcl = C.SETUP_TCL + TPL.replace("__PAGE__", page).replace("__SETS__", sets)
    import bridge as br, time
    br.BRIDGE.ensure()
    for _ in range(30):
        if br.BRIDGE.all_sessions():
            break
        time.sleep(1)
    print(C.cap(tcl, 90))
