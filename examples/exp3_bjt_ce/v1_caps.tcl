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
    if { $rn == "C1" || $rn == "C2" } {
        catch { $pl SetEffectivePropStringValue [DboTclHelper_sMakeCString "VALUE"] [DboTclHelper_sMakeCString "10uF"] }
        lappend out "$rn -> 10uF"
    } elseif { $rn == "Ce" } {
        catch { $pl SetEffectivePropStringValue [DboTclHelper_sMakeCString "VALUE"] [DboTclHelper_sMakeCString "47uF"] }
        lappend out "$rn -> 47uF"
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
