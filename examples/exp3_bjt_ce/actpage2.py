# -*- coding: utf-8 -*-
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br
import win32gui, win32con, win32api

frame = win32gui.FindWindow("OrCaptureFrame", None)
win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
win32gui.SetForegroundWindow(frame)
time.sleep(0.5)
s = None
for _ in range(20):
    try:
        s = br.BRIDGE.session()
        break
    except Exception as e:
        time.sleep(1)
if s is None:
    print("no agent")
    sys.exit(1)
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
