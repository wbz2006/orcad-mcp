set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set ADD { {440 240 440 190} {440 280 440 320} {650 320 840 320} {840 320 840 290} }
foreach s $ADD {
    set x1 [lindex $s 0]; set y1 [lindex $s 1]; set x2 [lindex $s 2]; set y2 [lindex $s 3]
    set w [$pg NewWireScalar $st [DboTclHelper_sMakeCPoint $x1 $y1] [DboTclHelper_sMakeCPoint $x2 $y2]]
    lappend out "add $x1,$y1-$x2,$y2"
}
foreach pt { {440 190} {440 320} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    set js [DboState]
    $pg AddJunctionToWire $p $js
    lappend out "junction $pt -> $js"
}
set n 0
set it [$pg NewWiresIter $st]; set w [$it NextWire $st]
while {$w != $null} { incr n; set w [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
lappend out "wires=$n"
return $out
