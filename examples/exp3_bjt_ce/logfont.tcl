set f [DboTclHelper_sMakeLOGFONT]
set out {}
lappend out "obj=$f"
lappend out "cmds=[info commands $f*]"
lappend out "conf=[catch { $f configure } r] -> $r"
return $out
