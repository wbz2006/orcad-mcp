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
    if { $rn == "RL" || $rn == "Rb1" } {
        lappend out "PART $rn"
        set dit [$pl NewDisplayPropsIter $st]
        set d [$dit NextProp $st]
        while { $d != $null } {
            set nm [DboTclHelper_sMakeCString]
            $d GetName $nm
            set n [DboTclHelper_sGetConstCharPtr $nm]
            set ds [DboState]
            set rot [$d GetRotation $ds]
            set xx [DboDisplayProp_sGetLocationX $d $ds]
            set yy [DboDisplayProp_sGetLocationY $d $ds]
            set vis [$d GetDisplayType $ds]
            lappend out "  prop=$n rot=$rot loc=$xx,$yy type=$vis"
            set d [$dit NextProp $st]
        }
        catch { delete_DboDisplayPropsIter $dit }
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
