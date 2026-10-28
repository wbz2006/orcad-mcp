import sys, os, time; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui, win32con
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
frame = win32gui.FindWindow("OrCaptureFrame", None)
win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
win32gui.BringWindowToTop(frame)
win32gui.SetWindowPos(frame, -1, 0,0,0,0, 0x0002|0x0001)
time.sleep(1.5)
from PIL import ImageGrab
img = ImageGrab.grab()
img.save(os.path.join(BASE, "screen47.png"))
print(img.size, win32gui.GetWindowRect(frame))
