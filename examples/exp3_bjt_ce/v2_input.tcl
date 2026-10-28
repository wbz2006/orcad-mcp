set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
# ---- moves ----
array set MOV {Rs {190 380} C1 {260 380} Vs {80 490}}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set c [DboTclHelper_sMakeCString]; $pl GetReference $c
    set rn [DboTclHelper_sGetConstCharPtr $c]
    if { [info exists MOV($rn)] } {
        set xy $MOV($rn)
        catch { $pl SetLocation [DboTclHelper_sMakeCPoint [lindex $xy 0] [lindex $xy 1]] }
        set l [$pl GetLocation $st]
        lappend out "move $rn -> [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
# ---- delete wires ----
set DEL { {280 440 280 390} {220 440 250 440} {90 380 90 340} {90 340 160 340} {160 340 160 440} {160 440 180 440} {90 420 90 590} }
set dels {}
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
while { $w != $null } {
    set a [$w GetStartPoint $st]; set b [$w GetEndPoint $st]
    set p1 [list [DboTclHelper_sGetCPointX $a] [DboTclHelper_sGetCPointY $a]]
    set p2 [list [DboTclHelper_sGetCPointX $b] [DboTclHelper_sGetCPointY $b]]
    foreach s $DEL {
        set q1 [lrange $s 0 1]; set q2 [lrange $s 2 3]
        if { ( $p1 == $q1 && $p2 == $q2 ) || ( $p1 == $q2 && $p2 == $q1 ) } { lappend dels $w; lappend out "del $q1-$q2"; break }
    }
    set w [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
foreach w $dels { catch { $pg DeleteWire $w } }
# ---- add wires ----
set ADD { {90 480 90 390} {90 390 180 390} {90 520 90 590} {220 390 250 390} }
foreach s $ADD {
    set x1 [lindex $s 0]; set y1 [lindex $s 1]; set x2 [lindex $s 2]; set y2 [lindex $s 3]
    set w [$pg NewWireScalar $st [DboTclHelper_sMakeCPoint $x1 $y1] [DboTclHelper_sMakeCPoint $x2 $y2]]
    lappend out "add $x1,$y1-$x2,$y2"
}
set n 0
set it2 [$pg NewWiresIter $st]; set w [$it2 NextWire $st]
while {$w != $null} { incr n; set w [$it2 NextWire $st] }
catch { delete_DboPageWiresIter $it2 }
lappend out "wires=$n"
return $out
