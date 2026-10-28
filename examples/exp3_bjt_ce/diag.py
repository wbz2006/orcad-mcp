import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui
f = win32gui.FindWindow("OrCaptureFrame", None)
print("frame", f, win32gui.GetWindowText(f), win32gui.GetWindowRect(f))
print("fg", win32gui.GetForegroundWindow(), win32gui.GetWindowText(win32gui.GetForegroundWindow()))
res=[]
def cb(h,_):
    if win32gui.IsWindowVisible(h):
        c=win32gui.GetClassName(h)
        if c=="#32770": res.append((h,win32gui.GetWindowText(h)))
win32gui.EnumWindows(cb,None)
print("dialogs", res)
