set pg [GetActivePage]
set st [DboState]
set out {}
foreach pt { {440 410} {440 470} {440 510} {440 590} {630 470} {630 500} {630 590} {570 590} {570 460} {900 190} {900 230} {330 390} {440 190} {440 320} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    lappend out "$pt = [$pg GetConnectionCount $p $st]"
}
return $out
