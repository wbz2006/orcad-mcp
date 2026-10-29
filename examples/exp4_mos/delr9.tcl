set st [DboState]
set out {}
OPage {SCHEMATIC1} {PAGE3}
catch { UnSelectAll }
set rc0 [catch { SelectObjectById 86 1 } e0]
set rc [catch { Delete } e]
lappend out "del R9 rc0=$rc0/$e0 rc=$rc/$e"
return $out
