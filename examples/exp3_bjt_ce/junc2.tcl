set pg [GetActivePage]
set st [DboState]
set p [DboTclHelper_sMakeCPoint 440 190]
set out {}
lappend out "count_before=[$pg GetConnectionCount $p $st]"
set js [DboState]
set r [$pg AddJunctionToWire $p $js]
lappend out "ret=$r"
lappend out "count_after=[$pg GetConnectionCount $p $st]"
set n 0
set it [$pg NewWiresIter $st]; set w [$it NextWire $st]
while {$w != $null} { incr n; set w [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
lappend out "wires=$n"
return $out
