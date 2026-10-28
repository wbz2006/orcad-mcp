set pg [GetActivePage]
set st [DboState]
set out {}
foreach pt { {90 390} {90 480} {90 520} {90 590} {180 390} {220 390} {250 390} {280 390} {330 390} {570 590} {900 190} {900 230} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    lappend out "$pt = [$pg GetConnectionCount $p $st]"
}
return $out
