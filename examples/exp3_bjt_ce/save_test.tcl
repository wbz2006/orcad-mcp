set _s $::DboSession_s_pDboSession
DboSession -this $_s
set st [DboState]
set d [$_s GetActiveDesign]
if { $d == "NULL" } { return "no active design" }
set nm [DboTclHelper_sMakeCString]
catch { $d GetName $nm }
set r [$_s SaveDesign $d]
return "design=[DboTclHelper_sGetConstCharPtr $nm] state=$r"
