set pg [GetActivePage]
set st [DboState]
set out {}
foreach pt { {440 190} {440 240} {440 280} {440 320} {440 370} {620 320} {650 320} {840 320} {840 290} {840 330} {900 190} {900 230} {570 590} {840 590} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    lappend out "$pt = [$pg GetConnectionCount $p $st]"
}
return $out
