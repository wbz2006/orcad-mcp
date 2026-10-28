set out {}
set pg [GetActivePage]
set st [DboState]
set null NULL
set it [$pg NewGlobalsIter $st]
set g [$it NextGlobal $st]
while { $g != $null } {
    set l [$g GetLocation $st]
    lappend out "GLOB [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"
    set g [$it NextGlobal $st]
}
catch { delete_DboPageGlobalsIter $it }
set nw 0
set wit [$pg NewWiresIter $st]; set w [$wit NextWire $st]
while {$w != $null} { incr nw; set w [$wit NextWire $st] }
catch {delete_DboPageWiresIter $wit}
lappend out "WIRES $nw"
return $out
