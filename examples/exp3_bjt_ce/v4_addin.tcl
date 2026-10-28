set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set ADD { {90 480 90 390} {90 390 180 390} {90 520 90 590} {220 390 250 390} }
foreach s $ADD {
    set x1 [lindex $s 0]; set y1 [lindex $s 1]; set x2 [lindex $s 2]; set y2 [lindex $s 3]
    set w [$pg NewWireScalar $st [DboTclHelper_sMakeCPoint $x1 $y1] [DboTclHelper_sMakeCPoint $x2 $y2]]
    lappend out "add $x1,$y1-$x2,$y2"
}
set n 0
set it [$pg NewWiresIter $st]; set w [$it NextWire $st]
while {$w != $null} { incr n; set w [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
lappend out "wires=$n"
return $out
