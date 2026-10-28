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
rect = win32gui.GetWindowRect(frame)
win32api.SetCursorPos(((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2))
time.sleep(0.2)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); time.sleep(0.08)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0); time.sleep(0.5)
# Place Part dialog
win32api.keybd_event(ord("P"), 0, 0, 0); time.sleep(0.08)
win32api.keybd_event(ord("P"), 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(2.0)
print("fg:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
