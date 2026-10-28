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
    set ds [DboState]
    set rot [catch { $pl GetRotation $ds } rv]
    set mir [catch { $pl GetMirrorType $ds } mv]
    lappend out "$rn rot=$rv mirror=$mv"
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
