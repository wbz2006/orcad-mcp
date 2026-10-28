set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set c [DboTclHelper_sMakeCString]; $pl GetReference $c; set rn [DboTclHelper_sGetConstCharPtr $c]
    if { $rn == "Vcc" } {
        set r1 [$pl SetRotation 0]
        set np [DboTclHelper_sMakeCPoint 950 190]
        set r2 [$pl SetLocation $np]
        set l [$pl GetLocation $st]
        lappend out "Vcc loc=[DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l] rot=$r1/$r2"
        set pit [$pl NewPinsIter $st]
        set p [$pit NextPin $st]
        while { $p != $null } {
            set pn "?"; catch { set c2 [DboTclHelper_sMakeCString]; $p GetPinName $c2; set pn [DboTclHelper_sGetConstCharPtr $c2] }
            set h [$p GetOffsetHotSpot $st]
            lappend out "pin $pn @ [DboTclHelper_sGetCPointX $h],[DboTclHelper_sGetCPointY $h]"
            set p [$pit NextPin $st]
        }
        catch { delete_DboPartInstPinsIter $pit }
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
