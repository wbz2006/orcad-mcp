# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp\examples\exp4_mos")
import exp4_common as C

PSP = "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice"
CAPSYM = "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/capsym.olb"

TPL = r'''
set out {}
set st [DboState]
proc orPlace2 { page libPath pkg partName name x y {rot 0} } {
    set st [DboState]
    set lib [$::gExpSession GetLib [orCStr $libPath] $st]
    if { $lib eq "NULL" } { error "GetLib failed $libPath" }
    set p [$lib GetPart [orCStr "$partName.Normal"] $st]
    if { $p eq "NULL" } { error "GetPart failed $partName" }
    set dev [[$p GetPackagePtr] GetDevice 0 $st]
    set xd [expr {round($x * $::gGran)}]
    set yd [expr {round($y * $::gGran)}]
    set loc [DboTclHelper_sMakeCPoint $xd $yd]
    set inst [$page NewPlacedInst $st [orCStr $name] [orCStr $pkg] $p $dev $loc $rot]
    if { $inst eq "NULL" } { error "NewPlacedInst failed $name" }
    return $inst
}
proc addTB { pg } {
    set st [DboState]
    set tit [$pg NewTitleBlocksIter $st]
    set tb [$tit NextTitleBlock $st]
    catch { delete_DboPageTitleBlocksIter $tit }
    if { $tb ne "NULL" } { return "tb exists" }
    set p1 [orGetPage exp4 PAGE1]
    set t2 [$p1 NewTitleBlocksIter $st]
    set src [$t2 NextTitleBlock $st]
    catch { delete_DboPageTitleBlocksIter $t2 }
    $pg NewTitleBlock $src $st
    return "tb copied"
}
set pg [orGetPage exp4 __PAGE__]
OPage {SCHEMATIC1} {__PAGE__}
set pg [GetActivePage]
$pg SetPageWidth 9700
$pg SetPageHeight 7200
lappend out "page __PAGE__ size=[$pg GetPageWidth]x[$pg GetPageHeight]"
lappend out [addTB $pg]
set r1 [orPlace2 $pg {%(psp)s/analog.olb} R R R1 5.9 2.8 1]
set m2 [orPlace2 $pg {%(psp)s/breakout.olb} Mbreakn Mbreakn M2 6.0 3.8 0]
set v1 [orPlace2 $pg {%(psp)s/source.olb} VDC VDC V1 4.0 1.8 0]
__SOURCE__
orSetActiveProp $r1 VALUE __RVAL__
orSetActiveProp $v1 DC 5V
__PROPS__
foreach w { {4.1 1.8 6.0 1.8} {6.0 1.8 6.0 2.7} {6.0 3.1 6.0 3.8} {6.0 3.8 6.2 3.8} {2.7 4.6 2.7 4.0} {2.7 4.0 5.9 4.0} {2.7 5.0 2.7 5.6} {4.1 2.2 4.1 2.6} {6.2 4.2 6.2 4.7} {6.2 4.7 6.2 4.9} {6.3 4.3 6.5 4.3} {6.5 4.3 6.5 4.7} {6.5 4.7 6.2 4.7} } {
    set rc [catch { PlaceWire [lindex $w 0] [lindex $w 1] [lindex $w 2] [lindex $w 3] } ew]
    if { $rc != 0 } { lappend out "wire $w FAIL $ew" }
}
foreach g { {4.1 2.6} {2.7 5.6} {6.2 4.9} } {
    set rc [catch { PlaceGround [lindex $g 0] [lindex $g 1] {%(capsym)s} {GND} {GND} } eg]
    if { $rc != 0 } { lappend out "gnd $g FAIL $eg" }
}
lappend out "parts=[$pg GetPartInstCount $st] wires=[$pg GetWireCount $st]"
set rc [catch { PlaceText 1.0 6.2 6.0 6.6 {__CAPTION__} } et]
lappend out "text rc=$rc e=$et save=[catch { Menu {File::Save} } es]"
return $out
'''

def build(page, src_kind, rval, caption):
    if src_kind == "dc":
        source = "set v2 [orPlace2 $pg {%s/source.olb} VDC VDC V2 2.6 4.6 0]" % PSP
        props = "orSetActiveProp $v2 DC 2V"
    else:
        source = "set v3 [orPlace2 $pg {%s/source.olb} VSIN VSIN V3 2.6 4.6 0]" % PSP
        props = ("orSetActiveProp $v3 VOFF 2.36\n"
                 "orSetActiveProp $v3 VAMPL 0.01\n"
                 "orSetActiveProp $v3 FREQ 1meg\n"
                 "orSetActiveProp $v3 AC 1")
    tcl = C.SETUP_TCL + TPL.replace("__PAGE__", page).replace("__SOURCE__", source) \
        .replace("__RVAL__", rval).replace("__PROPS__", props).replace("__CAPTION__", caption)
    tcl = tcl % {"psp": PSP, "capsym": CAPSYM}
    C.ensure_capture()
    print(C.cap(tcl, 120))

if __name__ == "__main__":
    build("PAGE4", "dc", "100k", "图4.24 无源负载共源放大器 R1=100k    信255_王保哲")
    build("PAGE5", "ac", "100k", "图4.25 交流小信号仿真电路 R1=100k    信255_王保哲")
