set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set kill {{90 90} {80 420} {320 489} {620 500} {830 330}}
set dels {}
set keep $null
set git [$pg NewGlobalsIter $st]
set g [$git NextGlobal $st]
while { $g != $null } {
    set l [$g GetLocation $st]
    set x [DboTclHelper_sGetCPointX $l]; set y [DboTclHelper_sGetCPointY $l]
    if { [lsearch -exact $kill [list $x $y]] >= 0 } { lappend dels $g; lappend out "del $x,$y" } else { set keep $g; lappend out "keep $x,$y" }
    set g [$git NextGlobal $st]
}
catch { delete_DboPageGlobalsIter $git }
foreach g $dels { set r [$pg DeleteGlobal $g]; lappend out "deleted $r" }
if { $keep != $null } { catch { $keep SetLocation [DboTclHelper_sMakeCPoint 560 590] } }
set n 0
set it [$pg NewGlobalsIter $st]; set g [$it NextGlobal $st]
while {$g != $null} { set l [$g GetLocation $st]; lappend out "left [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"; incr n; set g [$it NextGlobal $st] }
catch { delete_DboPageGlobalsIter $it }
lappend out "globals=$n"
return $out
