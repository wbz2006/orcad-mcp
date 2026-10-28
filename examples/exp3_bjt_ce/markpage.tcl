set pg [GetActivePage]
set st [DboState]
set r [$pg MarkModified]
return "marked $r isModified=[$pg IsModified $st]"
