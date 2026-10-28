set pg [GetActivePage]
set st [DboState]
set null NULL
set out {}
set n 0
catch {
  set it [$pg NewCommentGraphicsIter $st]
  set g [$it NextCommentGraphic $st]
  while { $g != $null } { incr n; lappend out "CG id=[$g GetId $st]"; set g [$it NextCommentGraphic $st] }
  catch { delete_DboPageCommentGraphicsIter $it }
}
lappend out "cg_count=$n"
set n2 0
catch {
  set it2 [$pg NewGraphicBoxInstsIter $st]
  set g2 [$it2 NextGraphicBoxInst $st]
  while { $g2 != $null } { incr n2; set g2 [$it2 NextGraphicBoxInst $st] }
}
lappend out "box=$n2"
return $out
