# -*- coding: utf-8 -*-
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br
import win32gui, win32con, win32api

SCALE = 1.5
profile = sys.argv[1] if len(sys.argv) > 1 else "Bias"


def click_phys(px, py):
    win32api.SetCursorPos((int(px / SCALE), int(py / SCALE)))
    time.sleep(0.15)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.08)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def activate(frame):
    win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
    time.sleep(0.3)
    for _ in range(4):
        try:
            win32gui.SetForegroundWindow(frame)
        except Exception:
            pass
        time.sleep(0.3)
        if win32gui.GetForegroundWindow() == frame:
            return True
    for _ in range(3):
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0); time.sleep(0.05)
        win32api.keybd_event(win32con.VK_TAB, 0, 0, 0); time.sleep(0.1)
        win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.05)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.8)
        if win32gui.GetForegroundWindow() == frame:
            return True
    return False


frame = win32gui.FindWindow("OrCaptureFrame", None)
print("activate:", activate(frame))
s = None
for _ in range(20):
    try:
        s = br.BRIDGE.session(); break
    except Exception:
        time.sleep(1)
print("select:", s.eval("SelectPMItem {%s}" % profile, 60))
time.sleep(0.6)
print("run:", s.eval('Menu "PSpice::Run"', 120))
time.sleep(4)
# report windows
rows = []
win32gui.EnumWindows(lambda h, _: rows.append((h, win32gui.GetClassName(h), win32gui.GetWindowText(h))) if win32gui.IsWindowVisible(h) and win32gui.GetWindowText(h) else None, None)
for h, c, t in rows:
    if "PSpice" in t or "pspice" in t or "Probe" in t or "Simulation" in t:
        print("WIN", hex(h), c, "|", t)
print("fg:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
