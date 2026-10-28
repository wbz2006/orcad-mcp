# -*- coding: utf-8 -*-
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con, win32api

SCALE = 1.5
frame = win32gui.FindWindow("OrCaptureFrame", None)


def click_phys(px, py, wait=0.6):
    win32api.SetCursorPos((int(px / SCALE), int(py / SCALE)))
    time.sleep(0.15)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(wait)


win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
try:
    win32gui.SetForegroundWindow(frame)
except Exception:
    pass
time.sleep(0.5)
if win32gui.GetForegroundWindow() != frame:
    for _ in range(4):
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0); time.sleep(0.05)
        win32api.keybd_event(win32con.VK_TAB, 0, 0, 0); time.sleep(0.1)
        win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.05)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.8)
        if win32gui.GetForegroundWindow() == frame:
            break
print("fg:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
click_phys(650, 50, 1.0)
print("opened")
