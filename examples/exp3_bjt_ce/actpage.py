# -*- coding: utf-8 -*-
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
dx.ensure_capture()
s = br.BRIDGE.session()
import win32gui, win32con, win32api
frame = win32gui.FindWindow("OrCaptureFrame", None)
rect = win32gui.GetWindowRect(frame)
win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
win32gui.BringWindowToTop(frame)
HWND_TOPMOST=-1; SWP_NOMOVE=0x0002; SWP_NOSIZE=0x0001
win32gui.SetWindowPos(frame, HWND_TOPMOST, 0,0,0,0, SWP_NOMOVE|SWP_NOSIZE)
time.sleep(0.4)
if win32gui.GetForegroundWindow() != frame:
    win32api.SetCursorPos((rect[0]+400, rect[1]+12))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0); time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0); time.sleep(0.6)
try:
    print("select:", s.eval('SelectPMItem {PAGE1}', 60))
except Exception as e:
    print("select err:", e)
time.sleep(0.5)
win32api.keybd_event(win32con.VK_RETURN,0,0,0)
win32api.keybd_event(win32con.VK_RETURN,0,win32con.KEYEVENTF_KEYUP,0)
time.sleep(3)
try:
    print("page:", s.eval('GetActivePage', 30))
except Exception as e:
    print("page err:", e)
