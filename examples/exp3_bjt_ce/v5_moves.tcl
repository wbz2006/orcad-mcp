set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
array set MOV {Rc {430 250} C2 {630 310}}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set c [DboTclHelper_sMakeCString]; $pl GetReference $c
    set rn [DboTclHelper_sGetConstCharPtr $c]
    if { [info exists MOV($rn)] } {
        set xy $MOV($rn)
        catch { $pl SetLocation [DboTclHelper_sMakeCPoint [lindex $xy 0] [lindex $xy 1]] }
        set l [$pl GetLocation $st]
        lappend out "move $rn -> [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
