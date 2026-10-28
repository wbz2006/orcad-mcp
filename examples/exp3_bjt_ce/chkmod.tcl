set pg [GetActivePage]
set st [DboState]
return "pageIsModified=[$pg IsModified $st]"
