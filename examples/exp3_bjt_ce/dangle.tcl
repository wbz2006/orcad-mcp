set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
unset -nocomplain seen
array set seen {}
set it [$pg NewWiresIter $st]
set w [$it NextWire $st]
while { $w != $null } {
    set a [$w GetStartPoint $st]; set b [$w GetEndPoint $st]
    foreach c [list $a $b] {
        set x [DboTclHelper_sGetCPointX $c]; set y [DboTclHelper_sGetCPointY $c]
        set seen($x,$y) 1
    }
    set w [$it NextWire $st]
}
catch { delete_DboPageWiresIter $it }
set cnt 0
foreach k [array names seen] {
    incr cnt
    set xy [split $k ","]
    set p [DboTclHelper_sMakeCPoint [lindex $xy 0] [lindex $xy 1]]
    set n [$pg GetConnectionCount $p $st]
    if { $n < 2 } { lappend out "DANGLING $k = $n" }
}
lappend out "endpoints=$cnt"
return $out
