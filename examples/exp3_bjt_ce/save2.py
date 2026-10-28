# -*- coding: utf-8 -*-
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui, win32con, win32api
DSN = r"D:\Users\Download\exp3_BJT_CE\EXP3.DSN"
frame = win32gui.FindWindow("OrCaptureFrame", None)
print("frame", hex(frame), "fg", hex(win32gui.GetForegroundWindow()))
rect = win32gui.GetWindowRect(frame)
win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
time.sleep(0.3)
try:
    win32gui.SetForegroundWindow(frame)
except Exception as e:
    print("setfg err", e)
time.sleep(0.5)
print("fg now", hex(win32gui.GetForegroundWindow()))
# click blank canvas inside page (page area roughly x 560..1950, y 460..1140)
win32api.SetCursorPos((1250, 980))
time.sleep(0.2)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0); time.sleep(0.08)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0); time.sleep(0.5)
print("fg after click", hex(win32gui.GetForegroundWindow()))
before = os.stat(DSN).st_mtime
win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0); time.sleep(0.06)
win32api.keybd_event(ord('S'), 0, 0, 0); time.sleep(0.12)
win32api.keybd_event(ord('S'), 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.06)
win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
t0=time.time()
ok=False
while time.time()-t0 < 25:
    time.sleep(0.5)
    m=os.stat(DSN).st_mtime
    if m!=before:
        print("SAVED %.1fs size=%d %s" % (time.time()-t0, os.stat(DSN).st_size, time.strftime("%H:%M:%S", time.localtime(m))))
        ok=True; break
if not ok:
    print("NO SAVE, fg=", hex(win32gui.GetForegroundWindow()), "title=", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
