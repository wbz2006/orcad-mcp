set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set DEL { {220 440 250 440} {90 420 90 590} }
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
set it [$pg NewWiresIter $st]; set w2 [$it NextWire $st]
while {$w2 != $null} { incr n; set w2 [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
lappend out "wires=$n"
return $out
