import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui
h = 59709222
print("dlg:", win32gui.GetWindowText(h))
res=[]
def cb(w,_):
    c=win32gui.GetClassName(w); t=win32gui.GetWindowText(w)
    if t or c in ("Button","Static","Edit"):
        res.append((c,t,w))
win32gui.EnumChildWindows(h, cb, None)
for c,t,w in res: print(c,"|",t)
