set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set c [DboTclHelper_sMakeCString]
    $pl GetReference $c
    set rn [DboTclHelper_sGetConstCharPtr $c]
    set v [DboTclHelper_sMakeCString]
    catch { $pl GetPartValue $v }
    set val [DboTclHelper_sGetConstCharPtr $v]
    lappend out "$rn = $val rot=[$pl GetRotation $st]"
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
