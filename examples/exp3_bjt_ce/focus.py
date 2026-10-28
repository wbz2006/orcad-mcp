# -*- coding: utf-8 -*-
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con, win32api

frame = win32gui.FindWindow("OrCaptureFrame", None)
print("frame", hex(frame), win32gui.GetWindowText(frame))
win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
time.sleep(0.4)
try:
    win32gui.SetForegroundWindow(frame)
except Exception as e:
    print("setfg err", e)
time.sleep(0.6)
print("fg", hex(win32gui.GetForegroundWindow()))
rect = win32gui.GetWindowRect(frame)
print("rect", rect)
# click an empty spot in the schematic canvas
win32api.SetCursorPos(((rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2))
time.sleep(0.2)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
time.sleep(0.08)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
time.sleep(0.8)
print("fg after click", hex(win32gui.GetForegroundWindow()))
print("title", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
