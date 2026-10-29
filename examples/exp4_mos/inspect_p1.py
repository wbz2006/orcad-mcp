# -*- coding: utf-8 -*-
"""Read-only inspection of EXP4 PAGE1: dump parts (id/ref/lib/x/y) and wires.

Usage: python inspect_p1.py [port]
"""
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
os.environ.setdefault("ORCAD_MCP_PORT", sys.argv[1] if len(sys.argv) > 1 else "5177")
import bridge as br


def frame():
    res = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in t:
            res.append((h, t))
        return True
    win32gui.EnumWindows(cb, None)
    return res


def trees(f):
    out = []
    win32gui.EnumChildWindows(
        f, lambda h, _: out.append(h) if win32gui.GetClassName(h) == "SysTreeView32" else None, None)
    return out


def enter_tree(f):
    for t in trees(f):
        win32gui.PostMessage(t, win32con.WM_SETFOCUS, 0, 0)
        win32gui.PostMessage(t, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        win32gui.PostMessage(t, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        time.sleep(1.0)


DUMP_TCL = r'''
proc dumpP1 {} {
    set out {}
    set st [DboState]
    set pg [GetActivePage]
    set it [$pg NewPartInstsIter $st]
    set i [$it NextPartInst $st]
    while { $i != "NULL" } {
        set pl [DboPartInstToDboPlacedInst $i]
        if { $pl ne "NULL" } {
            set c [DboTclHelper_sMakeCString]
            catch { $pl GetReference $c }
            set ref [DboTclHelper_sGetConstCharPtr $c]
            set lib "?"
            catch { $pl GetSourceLibName $c; set lib [DboTclHelper_sGetConstCharPtr $c] }
            set l [$pl GetLocation $st]
            set x [DboTclHelper_sGetCPointX $l]
            set y [DboTclHelper_sGetCPointY $l]
            set id "?"
            catch { set id [$pl GetId $st] }
            lappend out "PART id=$id ref=$ref lib=$lib loc=$x,$y"
        }
        set i [$it NextPartInst $st]
    }
    catch { delete_DboPagePartInstsIter $it }
    set wit [$pg NewWiresIter $st]
    set w [$wit NextWire $st]
    while { $w != "NULL" } {
        set a [$w GetStartPoint $st]
        set b [$w GetEndPoint $st]
        lappend out [format "WIRE %.2f,%.2f -> %.2f,%.2f" \
            [expr {[DboTclHelper_sGetCPointX $a]/100.0}] [expr {[DboTclHelper_sGetCPointY $a]/100.0}] \
            [expr {[DboTclHelper_sGetCPointX $b]/100.0}] [expr {[DboTclHelper_sGetCPointY $b]/100.0}]]
        set w [$wit NextWire $st]
    }
    catch { delete_DboPageWiresIter $it }
    lappend out "parts=[$pg GetPartInstCount $st] wires=[$pg GetWireCount $st]"
    return $out
}
if { [catch { dumpP1 } r] } { return "DUMP-ERR: $r" }
return $r
'''


def main():
    for h, t in frame():
        print("frame:", t)
    f = frame()[0][0] if frame() else None
    assert f, "Capture frame not found"
    s = None
    for _ in range(15):
        try:
            s = br.BRIDGE.session(); break
        except Exception:
            time.sleep(1)
    assert s, "no agent connected on port %s" % os.environ["ORCAD_MCP_PORT"]
    print("SESSION OK")
    try:
        print("select:", s.eval("SelectPMItem {PAGE1}", 60))
        enter_tree(f)
        print("page:", s.eval("GetActivePage", 30))
    except Exception as e:
        print("activate err:", e)
    print(s.eval(DUMP_TCL, 60))


if __name__ == "__main__":
    main()
