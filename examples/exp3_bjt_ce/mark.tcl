set pg [GetActivePage]
set st [DboState]
set out {}
foreach c {MarkModified} {
    if { [catch { set r [$pg $c] } e] } { lappend out "pg $c ERR $e" } else { lappend out "pg $c OK $r" }
}
if { [catch { set d [$pg GetDesign $st] } e] } { lappend out "GetDesign ERR $e" } else { lappend out "design=$d" }
if { [catch { set r [$d MarkModified] } e] } { lappend out "design MarkModified ERR $e" } else { lappend out "design MarkModified OK $r" }
return $out
