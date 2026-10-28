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
    if { $rn == "Rs" || $rn == "Rc" || $rn == "C1" || $rn == "C2" || $rn == "Vs" } {
        set line "$rn"
        set pit [$pl NewPinsIter $st]
        set p [$pit NextPin $st]
        while { $p != $null } {
            set pp [$p GetPinPosition $st]
            append line " ([DboTclHelper_sGetCPointX $pp],[DboTclHelper_sGetCPointY $pp])"
            set p [$pit NextPin $st]
        }
        catch { delete_DboPartInstPinsIter $pit }
        lappend out $line
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
