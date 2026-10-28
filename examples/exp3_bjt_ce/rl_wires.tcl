set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set w [$pg NewWireScalar $st [DboTclHelper_sMakeCPoint 840 320] [DboTclHelper_sMakeCPoint 840 435]]
lappend out "add1 $w"
set w2 [$pg NewWireScalar $st [DboTclHelper_sMakeCPoint 840 475] [DboTclHelper_sMakeCPoint 840 590]]
lappend out "add2 $w2"
set js [DboState]
set j [$pg AddJunctionToWire [DboTclHelper_sMakeCPoint 840 590] $js]
lappend out "junction $j"
set n 0
set it [$pg NewWiresIter $st]; set w [$it NextWire $st]
while {$w != $null} { incr n; set w [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
lappend out "wires=$n"
foreach pt { {840 320} {840 435} {840 475} {840 590} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    set jw [$pg GetWireAtJunction $p $st]
    lappend out "$pt conn=[$pg GetConnectionCount $p $st] junction=[expr {$jw != $null}]"
}
return $out
