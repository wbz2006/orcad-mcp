set out {}
lappend out "orPlacePart=[info commands orPlacePart]"
lappend out "orCStr=[info commands orCStr]"
lappend out "gExpSession=[info exists ::gExpSession]"
lappend out "gGran=[info exists ::gGran]"
return $out
