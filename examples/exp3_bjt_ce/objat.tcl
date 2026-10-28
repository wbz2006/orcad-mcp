set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
foreach pt { {840 330} {570 460} {550 190} {330 590} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    set it [$pg NewObjectsAtPointIter $p $st]
    set o [$it NextObject $st]
    set kinds {}
    while { $o != $null } {
        set k [$o GetObjectType]
        lappend kinds $k
        set o [$it NextObject $st]
    }
    catch { delete_DboPageObjectsAtPointIter $it }
    lappend out "$pt -> $kinds"
}
return $out
