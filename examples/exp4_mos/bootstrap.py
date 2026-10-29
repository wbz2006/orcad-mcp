# -*- coding: utf-8 -*-
"""Bootstrap exp4.dsn with PAGE1 and dump library part/pin geometry."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp4_common as C
import exp4lib

DSN = C.DSN
PSP = C.PSP
CAPSYM = C.CAPSYM


def main():
    exp4lib.generate_all()
    C.ensure_capture()
    # fresh design
    if os.path.exists(DSN.replace("/", "\\")):
        os.remove(DSN.replace("/", "\\"))
        print("removed old dsn")
    code = C.SETUP_TCL + r'''
set st [DboState]
set d [$::gExpSession CreateDesign $st [orCStr "%DSN%"] [orCStr "SCHEMATIC1"]]
if { $d == "NULL" } { error "CreateDesign failed" }
set vit [$d NewViewsIter $st $::IterDefs_SCHEMATICS]
set v [$vit NextView $st]
set sch [DboViewToDboSchematic $v]
if { $sch == "NULL" } { error "no schematic" }
set pg [$sch NewPage $st [orCStr "PAGE1"]]
if { $pg == "NULL" } { error "NewPage failed" }
set ::gExpPage $pg
set ::gGran [$pg GetPhysicalGranularity]
set sst [$::gExpSession SaveDesign $d]
return "design+page created"
'''.replace("%DSN%", DSN)
    print(C.cap(code, 180))

    # place candidate parts
    placements = [
        ("Q1", f"{PSP}/EVALAA.OLB", "VN2222", "VN2222", 4.0, 4.0, 0),
        ("M1", f"{PSP}/breakout.olb", "Mbreakn", "Mbreakn", 7.0, 4.0, 0),
        ("V1", f"{PSP}/source.olb", "VDC", "VDC", 3.0, 6.0, 0),
        ("V3", f"{PSP}/source.olb", "VSIN", "VSIN", 9.0, 6.0, 0),
        ("R1", f"{PSP}/analog.olb", "R", "R", 5.0, 2.0, 90),
    ]
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

    # ground via native command
    try:
        print(C.cap(C.SETUP_TCL + f'''
set pg [orGetPage exp4 PAGE1]
set r [catch {{ PlaceGround 6.0 7.0 "{CAPSYM}" "GND_POWER" 0 }} e]
return "ground rc=$r err=$e"
''', 90))
    except Exception as e:
        print("GND FAIL", e)

    # dump all parts + pins
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


if __name__ == "__main__":
    main()
