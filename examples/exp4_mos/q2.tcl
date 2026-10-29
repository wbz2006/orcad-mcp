set s $::DboSession_s_pDboSession
DboSession -this $s
set st [DboState]
set out {}
set it [$s NewDesignsIter $st]
set d [$it NextDesign $st]
set null NULL
while { $d != $null } {
    set nm [DboTclHelper_sMakeCString]; catch { $d GetName $nm }
    lappend out "design=[DboTclHelper_sGetConstCharPtr $nm]"
    set d [$it NextDesign $st]
}
return $out
