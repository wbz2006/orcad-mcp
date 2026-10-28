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


def activate():
    win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
    time.sleep(0.3)
    for _ in range(3):
        try:
            win32gui.SetForegroundWindow(frame)
        except Exception:
            pass
        time.sleep(0.3)
        if win32gui.GetForegroundWindow() == frame:
            return True
    for _ in range(4):
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0); time.sleep(0.05)
        win32api.keybd_event(win32con.VK_TAB, 0, 0, 0); time.sleep(0.1)
        win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.05)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.8)
        if win32gui.GetForegroundWindow() == frame:
            return True
    return False


print("activate:", activate())
click_phys(560, 100, 0.8)      # focus project manager area
click_phys(680, 50, 1.0)       # PSpice menu
click_phys(788, 266, 1.0)      # Simulate Selected Profile(s)
time.sleep(10)

rows = []
def cb(h, _):
    if win32gui.IsWindowVisible(h):
        t = win32gui.GetWindowText(h)
        if t:
            rows.append((h, win32gui.GetClassName(h), t))
win32gui.EnumWindows(cb, None)
for h, c, t in rows:
    if any(k in t for k in ("PSpice", "pspice", "Probe", "Simulation", "OrCAD")):
        print("WIN", hex(h), c, "|", t)
print("fg:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
