# -*- coding: utf-8 -*-
"""Place candidate exp4 parts on PAGE1 and dump geometry (no save)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp4_common as C

PSP = C.PSP
CAPSYM = C.CAPSYM

placements = [
    ("Q1", f"{PSP}/EVALAA.OLB", "VN2222", "VN2222", 4.0, 4.0, 0),
    ("M1", f"{PSP}/breakout.olb", "Mbreakn", "Mbreakn", 7.0, 4.0, 0),
    ("V1", f"{PSP}/source.olb", "VDC", "VDC", 3.0, 6.0, 0),
    ("V3", f"{PSP}/source.olb", "VSIN", "VSIN", 9.0, 6.0, 0),
    ("R1", f"{PSP}/analog.olb", "R", "R", 5.0, 2.0, 90),
]

C.ensure_capture()
print("page:", C.cap(C.SETUP_TCL + 'return [orGetPage exp4 PAGE1]', 60))
for name, lib, pkg, dev, x, y, rot in placements:
    tcl = C.SETUP_TCL + f'''
set pg [orGetPage exp4 PAGE1]
set inst [orPlacePart $pg "{lib}" "{pkg}" "{pkg}" "{dev}" "{name}" {x} {y} {rot}]
set sp [DboTclHelper_sMakeCString]; catch {{ $inst GetSourcePartName $sp }}
set sg [DboTclHelper_sMakeCString]; catch {{ $inst GetSourcePackageName $sg }}
set loc [$inst GetLocation [DboState]]
return "name={name} srcPart=[DboTclHelper_sGetConstCharPtr $sp] srcPkg=[DboTclHelper_sGetConstCharPtr $sg] loc=[DboTclHelper_sGetCPointX $loc],[DboTclHelper_sGetCPointY $loc] rot=[$inst GetRotation [DboState]] pins=[orPinList $inst]"
'''
    try:
        print(C.cap(tcl, 90))
    except Exception as e:
        print("PLACE FAIL", name, e)

try:
    print(C.cap(C.SETUP_TCL + f'''
set pg [orGetPage exp4 PAGE1]
set r [catch {{ PlaceGround 6.0 7.0 "{CAPSYM}" "GND_POWER" 0 }} e]
return "ground rc=$r err=$e"
''', 90))
except Exception as e:
    print("GND FAIL", e)

print(C.cap(C.SETUP_TCL + r'''
set pg [orGetPage exp4 PAGE1]
set st [DboState]
set out {}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set rn [DboTclHelper_sMakeCString]; catch { $pl GetReference $rn }
    set loc [$pl GetLocation $st]
    lappend out "[DboTclHelper_sGetConstCharPtr $rn] @ [DboTclHelper_sGetCPointX $loc],[DboTclHelper_sGetCPointY $loc] pins=[orPinList $pl]"
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
''', 90))
