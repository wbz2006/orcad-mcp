set st [DboState]
catch { UnSelectAll }
set rc [catch { SelectObjectById 45 1 } e]
return "rc=$rc e=$e"
