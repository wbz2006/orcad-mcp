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
            catch { $d GetName $nm }
            set n [DboTclHelper_sGetConstCharPtr $nm]
            set ds [DboState]
            set rot [catch { $d GetRotation $ds } rv]
            set lx [catch { $d sGetLocationX $d $ds } xx]
            set ly [catch { $d sGetLocationY $d $ds } yy]
            lappend out "  prop [$n] rot=$rv loc=$xx,$yy"
            set d [$dit NextProp $st]
        }
        catch { delete_DboDisplayPropsIter $dit }
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
