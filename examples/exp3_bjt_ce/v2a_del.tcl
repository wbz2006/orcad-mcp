set pg [GetActivePage]
set st [DboState]
set out {}
set null NULL
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
set n 0
set it2 [$pg NewWiresIter $st]; set w [$it2 NextWire $st]
while {$w != $null} { incr n; set w [$it2 NextWire $st] }
catch { delete_DboPageWiresIter $it2 }
lappend out "wires=$n"
return $out

