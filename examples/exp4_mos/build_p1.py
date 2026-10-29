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
OPage {SCHEMATIC1} {PAGE1}
set pg [GetActivePage]
set ::gGran [$pg GetPhysicalGranularity]
set v1 [orPlace2 $pg {C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/source.olb} VDC VDC V1 3.0 3.8 0]
set v2 [orPlace2 $pg {C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/source.olb} VDC VDC V2 7.0 2.6 0]
orSetActiveProp $v1 DC 3V
orSetActiveProp $v2 DC 5V
# rename Q1 by location
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set l [$pl GetLocation $st]
    set x [DboTclHelper_sGetCPointX $l]; set y [DboTclHelper_sGetCPointY $l]
    if { $x == 500 && $y == 360 } { $pl SetEffectivePropStringValue [orCStr Reference] [orCStr Q1] }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
foreach w { {3.1 3.8 4.9 3.8} {3.1 4.2 3.1 4.6} {5.2 3.5 5.2 2.6} {5.2 2.6 7.1 2.6} {7.1 3.0 7.1 3.4} {5.2 4.1 5.2 4.6} {5.4 3.8 5.7 3.8} {5.7 3.8 5.7 4.6} {5.7 4.6 5.2 4.6} } {
    set rc [catch { PlaceWire [lindex $w 0] [lindex $w 1] [lindex $w 2] [lindex $w 3] } ew]
    if { $rc != 0 } { lappend out "wire $w FAIL $ew" }
}
foreach g { {3.1 4.6} {7.1 3.4} {5.2 4.6} } {
    set rc [catch { PlaceGround [lindex $g 0] [lindex $g 1] {C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/capsym.olb} {GND} {GND} } eg]
    if { $rc != 0 } { lappend out "gnd $g FAIL $eg" }
}
lappend out "parts=[$pg GetPartInstCount $st] wires=[$pg GetWireCount $st]"
set rc [catch { PlaceText 1.0 6.2 6.0 6.6 {图4.3 增强型NMOS 特性测试电路    信255_王保哲} } et]
lappend out "text rc=$rc e=$et save=[catch { Menu {File::Save} } es]"
return $out
