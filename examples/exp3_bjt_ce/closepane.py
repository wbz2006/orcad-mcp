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
time.sleep(0.5)
# close the docked Place Part pane via its X (measured on 2560x1600 screenshot)
win32api.SetCursorPos((2430, 182))
time.sleep(0.2)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); time.sleep(0.08)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(1.0)
# click empty canvas to restore focus
win32api.SetCursorPos((1250, 1000))
time.sleep(0.2)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); time.sleep(0.08)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.8)
print("fg:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
