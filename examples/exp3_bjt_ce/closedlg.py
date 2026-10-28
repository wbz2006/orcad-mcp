import sys, time; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui, win32con
h = 59709222
try:
    b = win32gui.FindWindowEx(h, 0, "Button", None)
    # click &Close
    def cb(w,_):
        t = win32gui.GetWindowText(w)
        if t == "&Close":
            win32gui.SendMessage(w, win32con.BM_CLICK, 0, 0)
    win32gui.EnumChildWindows(h, cb, None)
    print("clicked")
except Exception as e:
    print("err", e)
time.sleep(3)
print("still:", win32gui.IsWindow(h))
