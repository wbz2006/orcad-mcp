set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
# 1) move Vcc inward
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    set c [DboTclHelper_sMakeCString]; $pl GetReference $c
    if { [DboTclHelper_sGetConstCharPtr $c] == "Vcc" } {
        catch { $pl SetLocation [DboTclHelper_sMakeCPoint 890 190] }
        set l [$pl GetLocation $st]
        lappend out "Vcc -> [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
# 2) delete 3 long wires
set dels {}
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
while { $w != $null } {
    set a [$w GetStartPoint $st]; set b [$w GetEndPoint $st]
    set p1 [list [DboTclHelper_sGetCPointX $a] [DboTclHelper_sGetCPointY $a]]
    set p2 [list [DboTclHelper_sGetCPointX $b] [DboTclHelper_sGetCPointY $b]]
    foreach pair { {{550 190} {960 190}} {{960 230} {960 590}} {{90 590} {960 590}} } {
        set q1 [lindex $pair 0]; set q2 [lindex $pair 1]
        if { ( $p1 == $q1 && $p2 == $q2 ) || ( $p1 == $q2 && $p2 == $q1 ) } {
            lappend dels $w; lappend out "del $p1 - $p2"
        }
    }
    set w [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
foreach w $dels { set r [$pg DeleteWire $w]; lappend out "deleted" }
set n 0
set it2 [$pg NewWiresIter $st]; set w [$it2 NextWire $st]
while {$w != $null} { incr n; set w [$it2 NextWire $st] }
catch { delete_DboPageWiresIter $it2 }
lappend out "wires=$n"
return $out
