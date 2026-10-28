# -*- coding: utf-8 -*-
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE); sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
import win32gui, win32con, win32api

def focus():
    frame = win32gui.FindWindow("OrCaptureFrame", None)
    rect = win32gui.GetWindowRect(frame)
    win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
    win32gui.BringWindowToTop(frame)
    win32gui.SetWindowPos(frame, -1, 0,0,0,0, 0x0002|0x0001)
    time.sleep(0.4)
    if win32gui.GetForegroundWindow() != frame:
        win32api.SetCursorPos((rect[0]+400, rect[1]+12))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0); time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0); time.sleep(0.8)
    return frame

f = focus()
print("foreground:", win32gui.GetForegroundWindow() == f)
win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
win32api.keybd_event(ord('S'), 0, 0, 0)
time.sleep(0.08)
win32api.keybd_event(ord('S'), 0, win32con.KEYEVENTF_KEYUP, 0)
win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(4)
print("title:", win32gui.GetWindowText(f))
st = os.stat(r"D:\Users\Download\exp3_BJT_CE\EXP3.DSN")
print("dsn mtime:", time.strftime("%H:%M:%S", time.localtime(st.st_mtime)), "now:", time.strftime("%H:%M:%S"))
