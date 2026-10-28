set pg [GetActivePage]
set st [DboState]
set out {}
set segs {
    {550 190 960 190}
    {960 230 960 590}
    {90 590 960 590}
    {90 420 90 590}
    {330 489 330 590}
    {570 510 570 590}
    {630 500 630 590}
    {840 330 840 590}
}
foreach s $segs {
    set x1 [lindex $s 0]; set y1 [lindex $s 1]; set x2 [lindex $s 2]; set y2 [lindex $s 3]
    set w [$pg NewWireScalar $st [DboTclHelper_sMakeCPoint $x1 $y1] [DboTclHelper_sMakeCPoint $x2 $y2]]
    if { $w == "NULL" } { lappend out "FAIL $x1,$y1-$x2,$y2" } else { lappend out "wire $x1,$y1-$x2,$y2" }
}
foreach j { {550 190} {330 590} {570 590} {630 590} {840 590} } {
    set p [DboTclHelper_sMakeCPoint [lindex $j 0] [lindex $j 1]]
    set r [$pg AddJunctionToWire $p $st]
    lappend out "junction $j -> $r"
}
set n 0
set it [$pg NewWiresIter $st]; set w [$it NextWire $st]
while {$w != $null} { incr n; set w [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
lappend out "wires=$n"
return $out
