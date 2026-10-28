set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set kill {{90 90} {80 420} {320 489} {620 500} {830 330}}
set git [$pg NewGlobalsIter $st]
set g [$git NextGlobal $st]
while { $g != $null } {
    set gnext [$git NextGlobal $st]
    set l [$g GetLocation $st]
    set x [DboTclHelper_sGetCPointX $l]
    set y [DboTclHelper_sGetCPointY $l]
    if { [lsearch -exact $kill [list $x $y]] >= 0 } {
        catch { $pg DeleteGlobal $g }
        lappend out "del $x,$y"
    } else {
        set np [DboTclHelper_sMakeCPoint 560 590]
        catch { $g SetLocation $np }
        lappend out "keep->560,590 was $x,$y"
    }
    set g $gnext
}
catch { delete_DboPageGlobalsIter $git }
return $out
