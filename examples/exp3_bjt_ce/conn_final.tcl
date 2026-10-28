set pg [GetActivePage]
set st [DboState]
set out {}
foreach pt { {900 190} {900 230} {90 480} {90 520} {90 590} {330 190} {440 190} {440 320} {440 370} {330 390} {330 590} {570 590} {840 590} {630 460} {570 460} {440 460} {840 320} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    lappend out "$pt = [$pg GetConnectionCount $p $st]"
}
return $out
