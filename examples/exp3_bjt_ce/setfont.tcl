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
        set f [DboLib_sGetDefaultPartValueFont $pl $st]
        lappend out "font=$f"
        set dit [$pl NewDisplayPropsIter $st]
        set d [$dit NextProp $st]
        while { $d != $null } {
            set nm [DboTclHelper_sMakeCString]; $d GetName $nm
            set n [DboTclHelper_sGetConstCharPtr $nm]
            if { $n == "Value" } {
                set r [catch { $d SetFont $f } rv]
                lappend out "setfont rc=$r val=$rv rot=[$d GetRotation $st]"
            }
            set d [$dit NextProp $st]
        }
        catch { delete_DboDisplayPropsIter $dit }
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
