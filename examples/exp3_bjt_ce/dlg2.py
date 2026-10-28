import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui
h = 5510058
print("dlg:", win32gui.GetWindowText(h))
def cb(w,_):
    t=win32gui.GetWindowText(w)
    if t: print(win32gui.GetClassName(w), "|", t)
win32gui.EnumChildWindows(h, cb, None)
