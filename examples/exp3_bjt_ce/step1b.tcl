set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set it [$pg NewGlobalsIter $st]
set g [$it NextGlobal $st]
while { $g != $null } {
    set l [$g GetLocation $st]
    set h [$g GetOffsetHotSpot $st]
    lappend out "GLOB loc=[DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l] hs=[DboTclHelper_sGetCPointX $h],[DboTclHelper_sGetCPointY $h]"
    set g [$it NextGlobal $st]
}
catch { delete_DboPageGlobalsIter $it }
return $out
