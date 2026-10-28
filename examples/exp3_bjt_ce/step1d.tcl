set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set target {620 500}
set git [$pg NewGlobalsIter $st]
set g [$git NextGlobal $st]
set found $null
while { $g != $null } {
    set l [$g GetLocation $st]
    set x [DboTclHelper_sGetCPointX $l]
    set y [DboTclHelper_sGetCPointY $l]
    if { $x == 620 && $y == 500 } { set found $g }
    set g [$git NextGlobal $st]
}
catch { delete_DboPageGlobalsIter $git }
if { $found != $null } { set r [$pg DeleteGlobal $found]; lappend out "del ok $r" } else { lappend out "not found" }
set n 0
set it [$pg NewGlobalsIter $st]; set g [$it NextGlobal $st]
while {$g != $null} { incr n; set g [$it NextGlobal $st] }
catch { delete_DboPageGlobalsIter $it }
lappend out "remaining=$n"
return $out
