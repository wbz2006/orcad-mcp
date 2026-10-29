set st [DboState]
catch { UnSelectAll }
set rc0 [catch { SelectObjectById 65 1 } e0]
set rc [catch { Delete } e]
return "sel=$rc0/$e0 del=$rc/$e"
