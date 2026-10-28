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
        set dit [$pl NewDisplayPropsIter $st]
        lappend out "iter=$dit"
        set d [$dit NextProp $st]
        lappend out "first=[list $d]"
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
