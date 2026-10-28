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
        time.sleep(0.35)
        if win32gui.GetForegroundWindow() == frame:
            return True
    # fallback: Alt+Tab to the previous window
    for _ in range(3):
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0); time.sleep(0.05)
        win32api.keybd_event(win32con.VK_TAB, 0, 0, 0); time.sleep(0.1)
        win32api.keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.05)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.8)
        if win32gui.GetForegroundWindow() == frame:
            return True
    # fallback: click title bar
    l, t, r, b = win32gui.GetWindowRect(frame)
    click_phys((l + r) / 2 * SCALE, (t + 12) * SCALE)
    time.sleep(0.6)
    return win32gui.GetForegroundWindow() == frame


frame = win32gui.FindWindow("OrCaptureFrame", None)
print("activate:", activate(frame), "fg:", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
s = None
for _ in range(20):
    try:
        s = br.BRIDGE.session(); break
    except Exception:
        time.sleep(1)
if s is None:
    print("no agent"); sys.exit(1)
try:
    print("select:", s.eval("SelectPMItem {PAGE1}", 60))
except Exception as e:
    print("select err:", e)
time.sleep(0.5)
win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(3)
try:
    print("page:", s.eval("GetActivePage", 30))
except Exception as e:
    print("page err:", e)
print("title:", win32gui.GetWindowText(frame))
