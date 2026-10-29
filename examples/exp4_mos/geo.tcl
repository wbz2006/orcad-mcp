set s $::DboSession_s_pDboSession
DboSession -this $s
set st [DboState]
set out {}
set it [$s NewDesignsIter $st]
set d [$it NextDesign $st]
set null NULL
while { $d != $null } {
    set nm [DboTclHelper_sMakeCString]; catch { $d GetName $nm }
    set dn [DboTclHelper_sGetConstCharPtr $nm]
    if { [string match -nocase *EXP3* $dn] || [string match -nocase *EXP4* $dn] } {
        set vit [$d NewViewsIter $st $::IterDefs_SCHEMATICS]
        set v [$vit NextView $st]
        while { $v != $null } {
            set vn [DboTclHelper_sMakeCString]; catch { $v GetName $vn }
            if { [string equal -nocase [DboTclHelper_sGetConstCharPtr $vn] SCHEMATIC1] } {
                set sch [DboViewToDboSchematic $v]
                set pit [$sch NewPagesIter $st]
                set pg [$pit NextPage $st]
                while { $pg != $null } {
                    set pn [DboTclHelper_sMakeCString]; catch { $pg GetName $pn }
                    set pname [DboTclHelper_sGetConstCharPtr $pn]
                    set w [$pg GetPageWidth]
                    set h [$pg GetPageHeight]
                    set g [$pg GetPhysicalGranularity]
                    lappend out "$dn $pname size=${w}x${h} gran=$g"
                    set iit [$pg NewPartInstsIter $st]
                    set i [$iit NextPartInst $st]
                    while { $i != $null } {
                        set pl [DboPartInstToDboPlacedInst $i]
                        set rn [DboTclHelper_sMakeCString]; catch { $pl GetReference $rn }
                        set l [$pl GetLocation $st]
                        lappend out "   [DboTclHelper_sGetConstCharPtr $rn] @ [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"
                        set i [$iit NextPartInst $st]
                    }
                    catch { delete_DboPagePartInstsIter $iit }
                    set pg [$pit NextPage $st]
                }
                catch { delete_DboSchematicPagesIter $pit }
            }
            set v [$vit NextView $st]
        }
        catch { delete_DboLibViewsIter $vit }
    }
    set d [$it NextDesign $st]
}
return $out
