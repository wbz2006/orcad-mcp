set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set target $null
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
while { $w != $null } {
    set a [$w GetStartPoint $st]; set b [$w GetEndPoint $st]
    set x1 [DboTclHelper_sGetCPointX $a]; set y1 [DboTclHelper_sGetCPointY $a]
    set x2 [DboTclHelper_sGetCPointX $b]; set y2 [DboTclHelper_sGetCPointY $b]
    if { $y1 == 190 && $y2 == 190 && [expr {$x1 <= 440 && $x2 >= 440}] } { set target $w }
    set w [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
if { $target == $null } { return "no bus" }
lappend out "bus=[$target GetId $st]"
lappend out "newjunc=[$target NewJunction [DboTclHelper_sMakeCPoint 440 190]]"
set n 0
set it [$pg NewWiresIter $st]; set w [$it NextWire $st]
while {$w != $null} { incr n; set w [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
lappend out "wires=$n"
set p [DboTclHelper_sMakeCPoint 440 190]
lappend out "conn=[$pg GetConnectionCount $p $st]"
return $out
