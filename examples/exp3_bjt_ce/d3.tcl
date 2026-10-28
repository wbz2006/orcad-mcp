set pg [GetActivePage]
set st [DboState]
set out {}
foreach pt { {330 590} {630 590} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    set r [$pg AddJunctionToWire $p $st]
    lappend out "junction $pt -> $r"
}
return $out
