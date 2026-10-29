set s $::DboSession_s_pDboSession
DboSession -this $s
set st [DboState]
set pg [GetActivePage]
set out {}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set rn [DboTclHelper_sMakeCString]; catch { $pl GetReference $rn }
    set l [$pl GetLocation $st]
    lappend out "[DboTclHelper_sGetConstCharPtr $rn] @ [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l] id=[$pl GetId $st]"
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
