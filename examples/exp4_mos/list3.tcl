set s $::DboSession_s_pDboSession
DboSession -this $s
set st [DboState]
set out {}
OPage {SCHEMATIC1} {PAGE3}
set pg [GetActivePage]
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set rn [DboTclHelper_sMakeCString]; catch { $pl GetReference $rn }
    set l [$pl GetLocation $st]
    lappend out "PART [DboTclHelper_sGetConstCharPtr $rn] @ [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l] id=[$pl GetId $st]"
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
while { $w != $null } {
    set a [$w GetStartPoint $st]
    set b [$w GetEndPoint $st]
    lappend out "WIRE [DboTclHelper_sGetCPointX $a],[DboTclHelper_sGetCPointY $a] -> [DboTclHelper_sGetCPointX $b],[DboTclHelper_sGetCPointY $b]"
    set w [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
return $out
