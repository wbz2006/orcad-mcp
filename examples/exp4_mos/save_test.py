# -*- coding: utf-8 -*-
"""Try to persist the in-memory exp4 design: MarkModified + posted Ctrl+S."""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp4_common as C
import win32gui, win32con

DSN = r"D:\Users\Download\try\EXP4.DSN"


def frame():
    res = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in win32gui.GetWindowText(h):
            res.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return res[0] if res else None


C.ensure_capture()
print("mark:", C.cap(C.SETUP_TCL + 'set d [$::gExpSession GetActiveDesign]; return [$d MarkModified]', 60))
f = frame()
print("frame", hex(f), repr(win32gui.GetWindowText(f)))
if f:
    win32gui.PostMessage(f, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
    win32gui.PostMessage(f, win32con.WM_KEYDOWN, ord('S'), 0)
    win32gui.PostMessage(f, win32con.WM_KEYUP, ord('S'), 0)
    win32gui.PostMessage(f, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)
for _ in range(20):
    time.sleep(0.5)
    print("exists", os.path.exists(DSN), os.path.getsize(DSN) if os.path.exists(DSN) else 0,
          "title", repr(win32gui.GetWindowText(f)) if f else "")
    if os.path.exists(DSN) and os.path.getsize(DSN) > 1000:
        break
