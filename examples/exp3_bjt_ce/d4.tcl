set pg [GetActivePage]
set st [DboState]
set out {}
foreach pt { {840 590} {570 590} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    set r [$pg AddJunctionToWire $p $st]
    lappend out "junction $pt -> $r"
}
return $out
