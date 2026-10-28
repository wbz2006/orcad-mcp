set r [Menu "Edit::Delete"]
set pg [GetActivePage]
set st [DboState]
set null NULL
set n 0
set it [$pg NewWiresIter $st]; set w [$it NextWire $st]
while {$w != $null} { incr n; set w [$it NextWire $st] }
catch { delete_DboPageWiresIter $it }
return "menu=$r wires=$n"
