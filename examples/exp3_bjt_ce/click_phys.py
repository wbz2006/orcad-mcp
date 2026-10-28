# -*- coding: utf-8 -*-
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con, win32api

SCALE = 1.5
px, py = float(sys.argv[1]), float(sys.argv[2])
win32api.SetCursorPos((int(px / SCALE), int(py / SCALE)))
time.sleep(0.4)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.1)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(2)
print("clicked", px, py)
print("fg:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
