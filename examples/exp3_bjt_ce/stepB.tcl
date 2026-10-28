set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set dels {}
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
while { $w != $null } {
    set a [$w GetStartPoint $st]
    set b [$w GetEndPoint $st]
    set ax [DboTclHelper_sGetCPointX $a]; set ay [DboTclHelper_sGetCPointY $a]
    set bx [DboTclHelper_sGetCPointX $b]; set by [DboTclHelper_sGetCPointY $b]
    set p1 [list $ax $ay]; set p2 [list $bx $by]
    if { ( $p1 == {100 130} && $p2 == {100 190} ) || ( $p1 == {100 190} && $p2 == {100 130} ) ||
         ( $p1 == {100 190} && $p2 == {330 190} ) || ( $p1 == {330 190} && $p2 == {100 190} ) } {
        lappend dels $w
        lappend out "del wire $ax,$ay-$bx,$by"
    }
    set w [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
foreach w $dels { set r [$pg DeleteWire $w]; lappend out "deleted $r" }
set n 0
set it2 [$pg NewWiresIter $st]; set w [$it2 NextWire $st]
while {$w != $null} { incr n; set w [$it2 NextWire $st] }
catch { delete_DboPageWiresIter $it2 }
lappend out "wires=$n"
return $out
