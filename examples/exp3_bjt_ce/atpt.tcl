set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
foreach pt { {440 190} {440 320} {570 590} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    lappend out "== $pt"
    set it [$pg NewObjectsAtPointIter $p $st]
    set o [$it NextObject $st]
    while { $o != $null } {
        lappend out "   id=[$o GetId $st]"
        set o [$it NextObject $st]
    }
    catch { delete_DboPageObjectsAtPointIter $it }
}
return $out
