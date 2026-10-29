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
    set loc [$pl GetLocation $st]
    lappend out "PART $rn @ [DboTclHelper_sGetCPointX $loc],[DboTclHelper_sGetCPointY $loc]"
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
set n 0
while { $w != $null } {
    set a [$w GetStartPoint $st]
    set b [$w GetEndPoint $st]
    lappend out "WIRE [DboTclHelper_sGetCPointX $a],[DboTclHelper_sGetCPointY $a] - [DboTclHelper_sGetCPointX $b],[DboTclHelper_sGetCPointY $b]"
    incr n
    set w [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
lappend out "WIRECOUNT $n"
set git [$pg NewPartInstsIter $st]
set g [$git NextPartInst $st]
while { $g != $null } {
    set c [DboTclHelper_sMakeCString]
    catch { $g GetReference $c }
    if { [DboTclHelper_sGetConstCharPtr $c] == "GND" } {
        set hs [$g GetOffsetHotSpot $st]
        lappend out "GND loc=[DboTclHelper_sGetCPointX $hs],[DboTclHelper_sGetCPointY $hs]"
    }
    set g [$git NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $git }
return $out
