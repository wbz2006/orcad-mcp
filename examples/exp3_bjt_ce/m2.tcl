set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
# delete 840,590-960,590
set dels {}
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
while { $w != $null } {
    set a [$w GetStartPoint $st]; set b [$w GetEndPoint $st]
    set p1 [list [DboTclHelper_sGetCPointX $a] [DboTclHelper_sGetCPointY $a]]
    set p2 [list [DboTclHelper_sGetCPointX $b] [DboTclHelper_sGetCPointY $b]]
    if { ( $p1 == {840 590} && $p2 == {960 590} ) || ( $p1 == {960 590} && $p2 == {840 590} ) } { lappend dels $w }
    set w [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
foreach w $dels { $pg DeleteWire $w; lappend out "del 840,590-960,590" }
foreach s { {550 190 900 190} {900 230 900 590} {840 590 900 590} } {
    set x1 [lindex $s 0]; set y1 [lindex $s 1]; set x2 [lindex $s 2]; set y2 [lindex $s 3]
    set w [$pg NewWireScalar $st [DboTclHelper_sMakeCPoint $x1 $y1] [DboTclHelper_sMakeCPoint $x2 $y2]]
    lappend out "wire $x1,$y1-$x2,$y2"
}
# Vcc pin check
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set c [DboTclHelper_sMakeCString]; $pl GetReference $c
    if { [DboTclHelper_sGetConstCharPtr $c] == "Vcc" } {
        set pit [$pl NewPinsIter $st]; set p [$pit NextPin $st]
        while { $p != $null } {
            set h [$p GetOffsetHotSpot $st]
            lappend out "Vcc pin @ [DboTclHelper_sGetCPointX $h],[DboTclHelper_sGetCPointY $h]"
            set p [$pit NextPin $st]
        }
        catch { delete_DboPartInstPinsIter $pit }
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
