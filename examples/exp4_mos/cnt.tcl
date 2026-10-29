set st [DboState]
set pg [GetActivePage]
return "parts=[$pg GetPartInstCount $st] wires=[$pg GetWireCount $st]"
