set out {}
lappend out "run=[catch { Menu "PSpice::Run" } r] -> $r"
return $out
