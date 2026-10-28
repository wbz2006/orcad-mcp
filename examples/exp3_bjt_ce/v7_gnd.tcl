set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set git [$pg NewGlobalsIter $st]
set g [$git NextGlobal $st]
while { $g != $null } {
    set h [$g GetOffsetHotSpot $st]
    set hx [DboTclHelper_sGetCPointX $h]; set hy [DboTclHelper_sGetCPointY $h]
    lappend out "found global hs=$hx,$hy"
    if { $hx == 570 && $hy == 590 } {
        catch { $g SetLocation [DboTclHelper_sMakeCPoint 430 590] }
        set l [$g GetLocation $st]; set h2 [$g GetOffsetHotSpot $st]
        lappend out "moved -> loc=[DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l] hs=[DboTclHelper_sGetCPointX $h2],[DboTclHelper_sGetCPointY $h2]"
    }
    set g [$git NextGlobal $st]
}
catch { delete_DboPageGlobalsIter $git }
return $out
