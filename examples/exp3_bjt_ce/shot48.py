import sys, os, time; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui, win32con, win32api
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
frame = win32gui.FindWindow("OrCaptureFrame", None)
rect = win32gui.GetWindowRect(frame)
win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
win32gui.BringWindowToTop(frame)
win32gui.SetWindowPos(frame, -1, 0,0,0,0, 0x0002|0x0001)
time.sleep(0.4)
if win32gui.GetForegroundWindow() != frame:
    win32api.SetCursorPos((rect[0]+400, rect[1]+12))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0); time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0); time.sleep(0.6)
win32api.SetCursorPos((rect[0]+300, rect[1]+900))
for _ in range(2):
    win32api.keybd_event(win32con.VK_ESCAPE,0,0,0); time.sleep(0.05)
    win32api.keybd_event(win32con.VK_ESCAPE,0,win32con.KEYEVENTF_KEYUP,0); time.sleep(0.3)
from PIL import ImageGrab
ImageGrab.grab().save(os.path.join(BASE, "screen48.png"))
print("ok")
