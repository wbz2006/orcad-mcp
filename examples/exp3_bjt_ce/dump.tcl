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
    set l [$pl GetLocation $st]
    lappend out "PART $rn @ [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
set n 0
while { $w != $null } {
    set a [$w GetStartPoint $st]; set b [$w GetEndPoint $st]
    lappend out "WIRE [DboTclHelper_sGetCPointX $a],[DboTclHelper_sGetCPointY $a] - [DboTclHelper_sGetCPointX $b],[DboTclHelper_sGetCPointY $b]"
    incr n
    set w [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
lappend out "WIRECOUNT $n"
set git [$pg NewGlobalsIter $st]
set g [$git NextGlobal $st]
while { $g != $null } {
    set l [$g GetLocation $st]; set h [$g GetOffsetHotSpot $st]
    lappend out "GND loc=[DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l] hs=[DboTclHelper_sGetCPointX $h],[DboTclHelper_sGetCPointY $h]"
    set g [$git NextGlobal $st]
}
catch { delete_DboPageGlobalsIter $git }
return $out
