set out {}
lappend out "sel=[SelectPMItem Bias]"
after 500
lappend out "run=[catch { Menu "PSpice::Run" } rv] -> $rv"
return $out
