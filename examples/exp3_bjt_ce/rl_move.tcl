set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set c [DboTclHelper_sMakeCString]; $pl GetReference $c
    set rn [DboTclHelper_sGetConstCharPtr $c]
    if { $rn == "RL" } {
        set r [$pl SetLocation [DboTclHelper_sMakeCPoint 830 445]]
        set l [$pl GetLocation $st]
        lappend out "RL -> $r [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
foreach pt { {840 290} {840 320} {840 330} {840 435} {840 475} {840 590} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    set jw [$pg GetWireAtJunction $p $st]
    lappend out "$pt conn=[$pg GetConnectionCount $p $st] junction=[expr {$jw != $null}]"
}
return $out
