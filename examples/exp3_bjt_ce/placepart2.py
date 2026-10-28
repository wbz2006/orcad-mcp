# -*- coding: utf-8 -*-
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con, win32api

frame = win32gui.FindWindow("OrCaptureFrame", None)
win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
win32gui.SetForegroundWindow(frame)
time.sleep(0.6)
print("fg:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
for _ in range(2):
    win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0); time.sleep(0.05)
    win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.3)
# toggle IME to english
win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0); time.sleep(0.06)
win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.4)
win32api.keybd_event(ord("P"), 0, 0, 0); time.sleep(0.1)
win32api.keybd_event(ord("P"), 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(2.5)
print("after P fg:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
