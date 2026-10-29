set st [DboState]
set out {}
OPage {SCHEMATIC1} {PAGE1}
set pg [GetActivePage]
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set ref [DboTclHelper_sMakeCString]
    catch { $pl GetReferenceDesignator $ref }
    set r [DboTclHelper_sGetConstCharPtr $ref]
    if { $r eq "V1" || $r eq "V2" } {
        lappend out "--- $r"
        set dit [$pl NewDisplayPropsIter]
        set d [$dit NextDisplayProp]
        while { $d != $null } {
            set nm [DboTclHelper_sMakeCString]
            catch { $d GetName $nm }
            set vv [DboTclHelper_sMakeCString]
            catch { $d GetValueString $vv }
            set dt [catch { $d GetDisplayType } x]
            lappend out "  prop=[DboTclHelper_sGetConstCharPtr $nm] val=[DboTclHelper_sGetConstCharPtr $vv] dt=$x"
            set d [$dit NextDisplayProp]
        }
        catch { delete_DboDisplayPropsIter $dit }
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
