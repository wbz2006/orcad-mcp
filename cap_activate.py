# -*- coding: utf-8 -*-
"""Activate a Capture schematic page without foreground / mouse / keyboard.

Usage:
  python cap_activate.py [PAGE1]

Why: GetActivePage raises "Command Requires SchematicView" when the page window
exists but is not the active *view*. SelectPMItem alone only selects the tree
node; posting Enter to the project tree (SysTreeView32) opens/activates it.
"""
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br


def frame():
    res = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in t:
            res.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return res[0] if res else None


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


def main():
    page = sys.argv[1] if len(sys.argv) > 1 else "PAGE1"
    f = frame()
    assert f, "Capture frame not found"
    s = None
    for _ in range(20):
        try:
            s = br.BRIDGE.session(); break
        except Exception:
            time.sleep(1)
    assert s, "Capture TCL agent not connected (ORCAD_MCP_PORT?)"
    try:
        print("select:", s.eval("SelectPMItem {%s}" % page, 60))
    except Exception as e:
        print("select err:", e)
    for _ in range(3):
        enter_tree(f)
        try:
            print("page:", s.eval("GetActivePage", 30))
            print("title:", win32gui.GetWindowText(f))
            return 0
        except Exception as e:
            print("retry:", e)
    return 1


if __name__ == "__main__":
    sys.exit(main())
