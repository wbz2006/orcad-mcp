set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set found $null
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
while { $w != $null } {
    set a [$w GetStartPoint $st]; set b [$w GetEndPoint $st]
    set p1 [list [DboTclHelper_sGetCPointX $a] [DboTclHelper_sGetCPointY $a]]
    set p2 [list [DboTclHelper_sGetCPointX $b] [DboTclHelper_sGetCPointY $b]]
    if { $p1 == {280 440} && $p2 == {280 390} } { set found $w }
    set w [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
if { $found != $null } { $pg DeleteWire $found; lappend out "deleted 280,440-280,390" }
set n 0
set it [$pg NewWiresIter $st]; set w2 [$it NextWire $st]
while {$w2 != $null} { incr n; set w2 [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
lappend out "wires=$n"
return $out
