set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set kill {{320 489} {620 500}}
set git [$pg NewGlobalsIter $st]
set g [$git NextGlobal $st]
while { $g != $null } {
    set gnext [$git NextGlobal $st]
    set l [$g GetLocation $st]
    set x [DboTclHelper_sGetCPointX $l]
    set y [DboTclHelper_sGetCPointY $l]
    if { [lsearch -exact $kill [list $x $y]] >= 0 } {
        set r [$pg DeleteGlobal $g]
        lappend out "del $x,$y -> $r"
    }
    set g $gnext
}
catch { delete_DboPageGlobalsIter $git }
set n 0
set it [$pg NewGlobalsIter $st]; set g [$it NextGlobal $st]
while {$g != $null} { incr n; set g [$it NextGlobal $st] }
catch { delete_DboPageGlobalsIter $it }
lappend out "remaining=$n"
return $out
