set pg [GetActivePage]
set st [DboState]
set out {}
foreach s { {90 590 960 590} {90 420 90 590} {330 489 330 590} {570 510 570 590} {630 500 630 590} {840 330 840 590} } {
    set x1 [lindex $s 0]; set y1 [lindex $s 1]; set x2 [lindex $s 2]; set y2 [lindex $s 3]
    set w [$pg NewWireScalar $st [DboTclHelper_sMakeCPoint $x1 $y1] [DboTclHelper_sMakeCPoint $x2 $y2]]
    lappend out "wire $x1,$y1-$x2,$y2 -> $w"
}
set n 0
set it [$pg NewWiresIter $st]; set w [$it NextWire $st]
while {$w != $null} { incr n; set w [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
lappend out "wires=$n"
return $out
