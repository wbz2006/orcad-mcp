set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set target $null
set wit [$pg NewWiresIter $st]
set w [$wit NextWire $st]
while { $w != $null } {
    set a [$w GetStartPoint $st]; set b [$w GetEndPoint $st]
    set p1 [list [DboTclHelper_sGetCPointX $a] [DboTclHelper_sGetCPointY $a]]
    set p2 [list [DboTclHelper_sGetCPointX $b] [DboTclHelper_sGetCPointY $b]]
    if { $p1 == {280 440} && $p2 == {280 390} } { set target $w }
    set w [$wit NextWire $st]
}
catch { delete_DboPageWiresIter $wit }
if { $target == $null } { return "not found" }
set id [$target GetId $st]
lappend out "id=$id"
lappend out "sel=[SelectObjectById $id]"
return $out
