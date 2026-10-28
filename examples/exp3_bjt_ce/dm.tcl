set pg [GetActivePage]
set st [DboState]
set d [$pg GetParentObj]
set out {}
lappend out "parent=$d"
catch { $d NoSuchMethodX } e
lappend out $e
return $out
