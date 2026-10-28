set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
foreach pt { {840 320} {840 435} {840 475} {840 590} {900 190} {900 230} {630 590} {440 590} {440 470} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    set jw [$pg GetWireAtJunction $p $st]
    lappend out "$pt conn=[$pg GetConnectionCount $p $st] junction=[expr {$jw != $null}]"
}
return $out
