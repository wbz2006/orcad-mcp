# -*- coding: utf-8 -*-
"""Unify PAGE1 grounds per manual fig 4.3: delete GND 801 (V1) & 805 (V2),
add bottom rail wires, junction at source node. Keep GND 809.

Save: MarkModified + foreground Ctrl+S (File::Save menu crashes Capture).
Usage: python fix_p1_gnd.py [port]
"""
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con, win32api
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
os.environ.setdefault("ORCAD_MCP_PORT", sys.argv[1] if len(sys.argv) > 1 else "5178")
import bridge as br

DSN = r"D:\Users\Download\try\EXP4.DSN"

FIX_TCL = r'''
proc fixP1 {} {
    set out {}
    set st [DboState]
    set pg [GetActivePage]
    # 1) delete GND 801 (V1) and 805 (V2) via native transaction
    foreach id {801 805} {
        catch { UnSelectAll }
        if { [catch { SelectObjectById $id } e] } { lappend out "SEL$id-ERR:$e"; continue }
        after 300
        if { [catch { Menu "Edit::Delete" } e] } { lappend out "DEL$id-ERR:$e" } else { lappend out "DEL$id-ok" }
        after 300
        catch { UnSelectAll }
    }
    # verify globals
    set g [$pg GetGlobalCount $st]
    lappend out "globals_after_del=$g"
    if { $g != 1 } { lappend out "ABORT: expected 1 global"; return $out }
    # 2) bottom rail wires (inches, y down)
    foreach w { {3.1 4.6 5.2 4.6} {7.1 3.4 7.1 4.6} {7.1 4.6 5.2 4.6} } {
        if { [catch { PlaceWire [lindex $w 0] [lindex $w 1] [lindex $w 2] [lindex $w 3] } e] } {
            lappend out "WIRE$w-ERR:$e"
        } else { lappend out "WIRE$w-ok" }
    }
    # 3) junction at source node (4-way point)
    if { [catch { PlaceJunction 5.2 4.6 } e] } { lappend out "JUNC-ERR:$e" } else { lappend out "JUNC-ok" }
    $pg MarkModified
    # 4) final dump
    set git [$pg NewGlobalsIter $st]
    set gg [$git NextGlobal $st]
    while { $gg != "NULL" } {
        set l [$gg GetLocation $st]
        set id "?"
        catch { set id [$gg GetId $st] }
        lappend out "GND id=$id loc=[DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]"
        set gg [$git NextGlobal $st]
    }
    catch { delete_DboGlobalsIter $git }
    set wit [$pg NewWiresIter $st]
    set w [$wit NextWire $st]
    set nw 0
    while { $w != "NULL" } {
        incr nw
        set a [$w GetStartPoint $st]
        set b [$w GetEndPoint $st]
        lappend out [format "W %.2f,%.2f->%.2f,%.2f" \
            [expr {[DboTclHelper_sGetCPointX $a]/100.0}] [expr {[DboTclHelper_sGetCPointY $a]/100.0}] \
            [expr {[DboTclHelper_sGetCPointX $b]/100.0}] [expr {[DboTclHelper_sGetCPointY $b]/100.0}]]
        set w [$wit NextWire $st]
    }
    catch { delete_DboPageWiresIter $wit }
    lappend out "total_wires=$nw"
    return $out
}
if { [catch { fixP1 } r] } { return "ERR: $r" }
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


def activate(f, s):
    trees = []
    win32gui.EnumChildWindows(f, lambda h, _: trees.append(h) if win32gui.GetClassName(h) == "SysTreeView32" else None, None)
    for t in trees:
        win32gui.PostMessage(t, win32con.WM_SETFOCUS, 0, 0)
        win32gui.PostMessage(t, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        win32gui.PostMessage(t, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        time.sleep(1.0)
    try:
        s.eval("SelectPMItem {PAGE1}", 60)
    except Exception:
        pass
    for t in trees:
        win32gui.PostMessage(t, win32con.WM_SETFOCUS, 0, 0)
        win32gui.PostMessage(t, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        win32gui.PostMessage(t, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        time.sleep(1.0)
    return s.eval("GetActivePage", 30)


def ctrl_s(f):
    win32gui.SetForegroundWindow(f)
    time.sleep(0.6)
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(ord('S'), 0, 0, 0)
    time.sleep(0.08)
    win32api.keybd_event(ord('S'), 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)


def main():
    f = frame()
    s = None
    for _ in range(15):
        try:
            s = br.BRIDGE.session(); break
        except Exception:
            time.sleep(1)
    assert s, "no agent"
    print("active:", activate(f, s))
    m0 = os.path.getmtime(DSN)
    r = s.eval(FIX_TCL, 120)
    print("\n".join(r) if isinstance(r, list) else r)
    if isinstance(r, list) and any(x.startswith("ERR") or "ABORT" in x for x in r):
        print(">>> NOT SAVING (errors above)")
        return 1
    time.sleep(1.0)
    ctrl_s(f)
    for _ in range(10):
        time.sleep(1)
        m1 = os.path.getmtime(DSN)
        if m1 != m0:
            print("SAVED, DSN mtime updated")
            break
    else:
        print("WARNING: DSN mtime unchanged - save may have failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
