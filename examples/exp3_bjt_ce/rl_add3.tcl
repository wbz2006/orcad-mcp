set pg [GetActivePage]
set st [DboState]
set out {}
set sess [$pg GetSession $st]
set lib [$sess GetLib [DboTclHelper_sMakeCString "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb"] $st]
set p [$lib GetPart [DboTclHelper_sMakeCString "R.Normal"] $st]
set inst [$pg NewPlacedInst $st [DboTclHelper_sMakeCString "RL"] [DboTclHelper_sMakeCString "R.Normal"] $p NULL [DboTclHelper_sMakeCPoint 830 445]]
lappend out "inst=$inst ok=[$st OK]"
if { $inst != "NULL" } {
    set r [$inst SetEffectivePropStringValue [DboTclHelper_sMakeCString "VALUE"] [DboTclHelper_sMakeCString "2k"]]
    lappend out "setvalue=$r ok=[$st OK]"
    set l [$inst GetLocation $st]
    lappend out "loc=[DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l] rot=[$inst GetRotation $st]"
}
return $out
