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
    if { $rn == "Rs" || $rn == "C1" || $rn == "Vs" || $rn == "C2" || $rn == "Rc" } {
        set l [$pl GetLocation $st]
        set line "$rn loc=[DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l] pins"
        set pit [$pl NewPinsIter $st]
        set p [$pit NextPin $st]
        while { $p != $null } {
            set h [$p GetHotSpot $st]
            append line " [DboTclHelper_sGetCPointX $h],[DboTclHelper_sGetCPointY $h]"
            set p [$pit NextPin $st]
        }
        catch { delete_DboPartInstPinsIter $pit }
        lappend out $line
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
