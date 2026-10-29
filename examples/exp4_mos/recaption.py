# -*- coding: utf-8 -*-
"""改某页 Place->Text 图注文字(值类修改, 安全)。用法: python recaption.py PAGE5 "新图注" """
import sys
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp\examples\exp4_mos")
import exp4_common as C

TPL = r'''
set st [DboState]
set out {}
OPage {SCHEMATIC1} {__PAGE__}
set pg [GetActivePage]
set it [$pg NewCommentGraphicsIter $st]
set g [$it NextCommentGraphic $st]
set null NULL
while { $g != $null } {
    set txt [DboGraphicCommentTextInst_sGetText $g $st]
    lappend out "old=<[DboTclHelper_sGetConstCharPtr $txt]>"
    set c [DboGraphicInstanceToDboGraphicCommentTextInst $g]
    set rc [catch { $c SetText [orCStr {__CAPTION__}] } e]
    lappend out "set rc=$rc"
    set g [$it NextCommentGraphic $st]
}
catch { delete_DboPageCommentGraphicsIter $it }
$pg MarkModified
lappend out "save=[catch { Menu {File::Save} } es]"
return $out
'''

if __name__ == "__main__":
    page, cap = sys.argv[1], sys.argv[2]
    import bridge as br, time
    br.BRIDGE.ensure()
    for _ in range(30):
        if br.BRIDGE.all_sessions():
            break
        time.sleep(1)
    tcl = C.SETUP_TCL + TPL.replace("__PAGE__", page).replace("__CAPTION__", cap)
    print(C.cap(tcl, 90))
