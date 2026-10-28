set pg [GetActivePage]
set st [DboState]
set out {}
foreach pt { {900 190} {900 230} {900 590} {840 590} {550 190} {90 590} {330 590} {570 590} {630 590} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    lappend out "$pt = [$pg GetConnectionCount $p $st]"
}
return $out
