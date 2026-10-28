# -*- coding: utf-8 -*-
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con, win32api

SCALE = 1.5  # physical pixels per logical pixel (DPI unaware process)

def click(px, py):
    """click at physical screen coords (2560x1600 screenshot space)"""
    win32api.SetCursorPos((int(px / SCALE), int(py / SCALE)))
    time.sleep(0.2)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.6)

frame = win32gui.FindWindow("OrCaptureFrame", None)
win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
win32gui.SetForegroundWindow(frame)
time.sleep(0.5)
click(2511, 185)   # X of Place Part pane
time.sleep(0.8)
click(1250, 1000)  # empty canvas
time.sleep(0.6)
print("fg:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
