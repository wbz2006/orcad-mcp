set pg [GetActivePage]
set st [DboState]
set out {}
set c [DboTclHelper_sMakeCString]
$pg GetName $c
lappend out "name=[DboTclHelper_sGetConstCharPtr $c]"
lappend out "modifyTime=[$pg GetModifyTime $st]"
lappend out "isModified=[$pg IsModified $st]"
lappend out "pageW=[$pg GetPageWidth] H=[$pg GetPageHeight]"
return $out
