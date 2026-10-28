set out {}
foreach d [GetOpenDesigns] {
    set n [DboTclHelper_sMakeCString]
    catch { $d GetName $n }
    set nm [DboTclHelper_sGetConstCharPtr $n]
    set p [DboTclHelper_sMakeCString]
    catch { $d GetPath $p }
    set pp [DboTclHelper_sGetConstCharPtr $p]
    lappend out "design $d name=[$nm] path=[$pp]"
}
lappend out "session=[GetSession]"
return $out
