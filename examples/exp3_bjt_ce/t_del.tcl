set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set w [$pg NewWireScalar $st [DboTclHelper_sMakeCPoint 700 700] [DboTclHelper_sMakeCPoint 800 700]]
lappend out "added $w"
set found $null
set wit [$pg NewWiresIter $st]
set w2 [$wit NextWire $st]
while { $w2 != $null } {
    set a [$w2 GetStartPoint $st]; set b [$w2 GetEndPoint $st]
    if { [DboTclHelper_sGetCPointX $a] == 700 && [DboTclHelper_sGetCPointY $a] == 700 } { set found $w2 }
    set w2 [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
if { $found != $null } { set r [$pg DeleteWire $found]; lappend out "deleted" } else { lappend out "not found" }
set n 0
set it [$pg NewWiresIter $st]; set w3 [$it NextWire $st]
while {$w3 != $null} { incr n; set w3 [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
lappend out "wires=$n"
return $out
