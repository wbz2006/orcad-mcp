set pg [GetActivePage]
set st [DboState]
set out {}
foreach pt { {960 190} {960 230} {90 590} {330 590} {570 590} {630 590} {840 330} {550 190} {90 420} {330 489} {570 510} {630 500} {90 380} {330 240} {550 240} {550 280} {440 370} {440 410} {420 390} {330 449} {330 280} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    lappend out "$pt = [$pg GetConnectionCount $p $st]"
}
return $out
