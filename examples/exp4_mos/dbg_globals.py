# -*- coding: utf-8 -*-
"""Debug: dump raw values of globals in the exact same loop shape as fix3."""
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
os.environ.setdefault("ORCAD_MCP_PORT", sys.argv[1] if len(sys.argv) > 1 else "5178")
import bridge as br

DBG = r'''
proc dbgP1 {} {
    set out {}
    set st [DboState]
    set pg [GetActivePage]
    set git [$pg NewGlobalsIter $st]
    set gg [$git NextGlobal $st]
    while { $gg != "NULL" } {
        set l [$gg GetLocation $st]
        set x [DboTclHelper_sGetCPointX $l]
        set y [DboTclHelper_sGetCPointY $l]
        set id "?"
        catch { set id [$gg GetId $st] }
        set nm "?"
        catch {
            set c [DboTclHelper_sMakeCString]
            $gg GetName $c
            set nm [DboTclHelper_sGetConstCharPtr $c]
        }
        lappend out "G id=$id name=$nm x=<$x> y=<$y> type_x=[tk::math::typeof $x] eq=[expr {$x == 310}]"
        set gg [$git NextGlobal $st]
    }
    catch { delete_DboGlobalsIter $git }
    return $out
}
if { [catch { dbgP1 } r] } { return "ERR: $r" }
return $r
'''


def frame():
    res = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in win32gui.GetWindowText(h):
            res.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return res[0]


def main():
    f = frame()
    s = None
    for _ in range(15):
        try:
            s = br.BRIDGE.session(); break
        except Exception:
            time.sleep(1)
    assert s, "no agent"
    trees = []
    win32gui.EnumChildWindows(f, lambda h, _: trees.append(h) if win32gui.GetClassName(h) == "SysTreeView32" else None, None)
    for t in trees:
        win32gui.PostMessage(t, win32con.WM_SETFOCUS, 0, 0)
        win32gui.PostMessage(t, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        win32gui.PostMessage(t, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        time.sleep(1.0)
    s.eval("SelectPMItem {PAGE1}", 60)
    for t in trees:
        win32gui.PostMessage(t, win32con.WM_SETFOCUS, 0, 0)
        win32gui.PostMessage(t, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        win32gui.PostMessage(t, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        time.sleep(1.0)
    print("page:", s.eval("GetActivePage", 30))
    r = s.eval(DBG, 60)
    print("\n".join(r) if isinstance(r, list) else r)


if __name__ == "__main__":
    main()
