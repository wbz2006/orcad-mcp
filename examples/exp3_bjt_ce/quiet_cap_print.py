# -*- coding: utf-8 -*-
"""Quiet Capture schematic print: no foreground, no mouse, no keyboard.

- activates PAGE1 through SelectPMItem + posted Enter on the project tree
- File>Print via posted WM_COMMAND
- print dialog: BM_CLICK on the default button
- Save As: WM_SETTEXT on the first visible Edit + WM_COMMAND IDOK
"""
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
import print_export as pe
import orcad_quiet as oq

OUT = sys.argv[1] if len(sys.argv) > 1 else r"D:\Users\Download\exp3_BJT_CE\_verify_schematic.pdf"


def find_frame():
    res = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in t:
            res.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return res[0] if res else None


def tree_enter(frame):
    trees = []
    win32gui.EnumChildWindows(
        frame, lambda h, _: trees.append(h) if win32gui.GetClassName(h) == "SysTreeView32" else None, None)
    for t in trees:
        win32gui.PostMessage(t, win32con.WM_SETFOCUS, 0, 0)
        win32gui.PostMessage(t, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        win32gui.PostMessage(t, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        time.sleep(1.2)


frame = find_frame()
assert frame, "Capture frame not found"
print("frame", hex(frame), win32gui.GetWindowText(frame))

# activate PAGE1 (Tcl select + posted Enter)
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp\examples\exp3_bjt_ce")
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br
s = None
for _ in range(15):
    try:
        s = br.BRIDGE.session(); break
    except Exception:
        time.sleep(1)
print("select:", s.eval("SelectPMItem {PAGE1}", 60))
tree_enter(frame)
try:
    print("page:", s.eval("GetActivePage", 30))
except Exception as e:
    print("page err:", e)

if os.path.exists(OUT):
    os.remove(OUT)
assert pe.menu_cmd(frame, "File", "Print"), "File>Print menu not found"
d = pe.find_dlg(pe.is_print_dlg, 10)
assert d, "print dialog not found"
print("print dialog", hex(d), repr(win32gui.GetWindowText(d)))
assert oq.bg_ok(d), "no default button in print dialog"
time.sleep(1.0)
d2 = pe.find_dlg(pe.is_saveas_dlg, 15)
assert d2, "save-as dialog not found"
print("save-as", hex(d2), repr(win32gui.GetWindowText(d2)))
e = next(w for w in pe.child_list(d2)
         if win32gui.GetClassName(w) == "Edit" and win32gui.IsWindowVisible(w))
win32gui.SendMessage(e, win32con.WM_SETTEXT, 0, OUT)
time.sleep(0.4)
win32gui.SendMessage(d2, win32con.WM_COMMAND, win32con.IDOK, 0)
t0 = time.time()
while time.time() - t0 < 20:
    if os.path.exists(OUT) and os.path.getsize(OUT) > 500:
        break
    time.sleep(0.4)
    oq.dismiss_dialogs(overwrite_yes=True)
print("pdf", os.path.exists(OUT), os.path.getsize(OUT) if os.path.exists(OUT) else 0)
