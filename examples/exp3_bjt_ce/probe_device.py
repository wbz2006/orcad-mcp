import sys, os, time
sys.path.insert(0, ".")
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx

dx.ensure_capture()
s = br.BRIDGE.session()

# R2 id=70 at (790,450), local pins (0,10),(20,10) → 假设1: 绝对=(790,460),(810,460)
print(s.eval(dx.SETUP_TCL + r'''
set pg [GetActivePage]
set st [DboState]
set out {}
# 旋转枚举尝试
set rv "?"
if { ![catch { set rv [DboTclHelper_sMakeDboValue 1] }] } {
    if { ![catch { set pl2 [$pg NewPartInstsIter $st]; set i2 [$pl2 NextPartInst $st]; set pl [DboPartInstToDboPlacedInst $i2]; $pl SetRotation $rv } e] } {
        lappend out "SetRotation(DboValue) ok"
    } else {
        lappend out "SetRotation(DboValue): $e"
    }
} else {
    lappend out "MakeDboValue: $rv"
}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $null } {
        set id "?"
        catch { set id [$pl GetId $st] }
        if { $id == 70 } {
            set lc [$pl GetLocation $st]
            set loc "[DboTclHelper_sGetCPointX $lc],[DboTclHelper_sGetCPointY $lc]"
            set gr1 "?"
            catch { set gr1 [$pl GetRotation] }
            set gr2 "?"
            catch { set gr2 [$pl GetRotation $st] }
            set pins [orPinList $pl]
            lappend out "R2 loc=$loc GetRotation()=$gr1 (st)=$gr2 pins=$pins"
        }
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
# 视觉测试:在假设的 pin 位置画线
if { [catch { PlaceWire 790.0 460.0 810.0 460.0 } e1] } { lappend out "wire1 err: $e1" } else { lappend out "wire1 ok" }
if { [catch { PlaceWire 790.0 460.0 790.0 560.0 } e2] } { lappend out "wire2 err: $e2" } else { lappend out "wire2 ok" }
return $out
''', 180))
