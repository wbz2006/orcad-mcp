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
    set ref [DboTclHelper_sGetConstCharPtr $rn]
    set l [$pl GetLocation $st]
    set x [DboTclHelper_sGetCPointX $l]
    set y [DboTclHelper_sGetCPointY $l]
    lappend out "PART $ref @ $x,$y"
    set hit [$pl NewPinsIter $st]
    set h [$hit NextPin $st]
    while { $h != $null } {
        set hn [DboTclHelper_sMakeCString]; catch { $h GetName $hn }
        set p [$h GetOffsetHotSpot $st]
        lappend out "   pin [DboTclHelper_sGetConstCharPtr $hn] off=[DboTclHelper_sGetCPointX $p],[DboTclHelper_sGetCPointY $p]"
        set h [$hit NextPin $st]
    }
    catch { delete_DboPartInstPinsIter $hit }
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
