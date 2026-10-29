# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp\examples\exp4_mos")
import exp4_common as C

PSP = "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice"
CAPSYM = "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/capsym.olb"

tcl = C.SETUP_TCL + r'''
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
set pg [orGetPage exp4 PAGE3]
set rc [catch { OPage {SCHEMATIC1} {PAGE3} } e]
lappend out "opage rc=$rc e=$e"
set pg [GetActivePage]
$pg SetPageWidth 9700
$pg SetPageHeight 7200
lappend out "size=[$pg GetPageWidth]x[$pg GetPageHeight] parts=[$pg GetPartInstCount $st]"
set tit [$pg NewTitleBlocksIter $st]
set tb [$tit NextTitleBlock $st]
catch { delete_DboPageTitleBlocksIter $tit }
if { $tb eq "NULL" } {
    set p1 [orGetPage exp4 PAGE1]
    set tit2 [$p1 NewTitleBlocksIter $st]
    set src [$tit2 NextTitleBlock $st]
    catch { delete_DboPageTitleBlocksIter $tit2 }
    set rc [catch { $pg NewTitleBlock $src $st } e2]
    lappend out "titleblock rc=$rc e=$e2"
} else {
    lappend out "titleblock already present"
}
set r1 [orPlace2 $pg {%(psp)s/analog.olb} R R R1 5.9 2.8 1]
set m2 [orPlace2 $pg {%(psp)s/breakout.olb} Mbreakn Mbreakn M2 6.0 3.8 0]
set v1 [orPlace2 $pg {%(psp)s/source.olb} VDC VDC V1 4.0 1.8 0]
set v3 [orPlace2 $pg {%(psp)s/source.olb} VSIN VSIN V3 2.6 4.6 0]
lappend out "placed parts=[$pg GetPartInstCount $st]"
orSetActiveProp $r1 VALUE 10k
orSetActiveProp $v1 DC 5V
orSetActiveProp $v3 VOFF 2.36
orSetActiveProp $v3 VAMPL 0.01
orSetActiveProp $v3 FREQ 1meg
orSetActiveProp $v3 AC 1
lappend out "props ok"
foreach w { {4.1 1.8 6.0 1.8} {6.0 1.8 6.0 2.7} {6.0 3.1 6.0 3.8} {6.0 3.8 6.2 3.8} {2.7 4.6 2.7 4.0} {2.7 4.0 5.9 4.0} {2.7 5.0 2.7 5.6} {6.2 4.2 6.2 4.7} {6.2 4.7 6.2 4.9} {6.3 4.3 6.5 4.3} {6.5 4.3 6.5 4.7} {6.5 4.7 6.2 4.7} } {
    set rc [catch { PlaceWire [lindex $w 0] [lindex $w 1] [lindex $w 2] [lindex $w 3] } ew]
    if { $rc != 0 } { lappend out "wire $w FAIL $ew" }
}
lappend out "wires=[$pg GetWireCount $st]"
foreach g { {4.1 2.6} {2.7 5.6} {6.2 4.9} } {
    set rc [catch { PlaceGround [lindex $g 0] [lindex $g 1] {%(capsym)s} {GND} {GND} } eg]
    if { $rc != 0 } { lappend out "gnd $g FAIL $eg" }
}
set rc [catch { PlaceText 1.0 6.2 5.8 6.6 {图4.21 交流小信号仿真电路 R1=10k    信255_王保哲} } et]
lappend out "text rc=$rc e=$et"
lappend out "save=[catch { Menu {File::Save} } es]"
return $out
''' % {"psp": PSP, "capsym": CAPSYM}

C.ensure_capture()
print(C.cap(tcl, 90))
