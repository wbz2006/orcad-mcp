set pg [GetActivePage]
set st [DboState]
set out {}
set sess [$pg GetSession $st]
lappend out "sess=$sess ok=[$st OK]"
set lib [$sess GetLib [DboTclHelper_sMakeCString "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb"] $st]
lappend out "lib=$lib ok=[$st OK]"
set p [$lib GetPart [DboTclHelper_sMakeCString "R.Normal"] $st]
lappend out "part=$p ok=[$st OK]"
return $out
