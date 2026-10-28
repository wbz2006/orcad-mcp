# -*- coding: utf-8 -*-
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con, win32api

def key(vk, wait=0.12):
    win32api.keybd_event(vk, 0, 0, 0); time.sleep(wait)
    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(wait)

key(ord("S"), 0.4)
key(win32con.VK_RETURN, 0.5)
time.sleep(12)
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
