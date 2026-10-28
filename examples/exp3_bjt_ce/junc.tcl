set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set it [$pg NewJunctionsIter $st]
set j [$it NextJunction $st]
while { $j != $null } {
    set l [$j GetLocation $st]
    lappend out "J [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"
    set j [$it NextJunction $st]
}
catch { delete_DboPageJunctionsIter $it }
return $out
