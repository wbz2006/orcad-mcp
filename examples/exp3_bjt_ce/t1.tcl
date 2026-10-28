set pg [GetActivePage]
set st [DboState]
set p [DboTclHelper_sMakeCPoint 550 190]
set r [$pg AddJunctionToWire $p $st]
return "junction 550,190 -> $r"
