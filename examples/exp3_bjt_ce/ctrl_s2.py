# -*- coding: utf-8 -*-
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui, win32con, win32api

def press_ctrl_s():
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(ord('S'), 0, 0, 0)
    time.sleep(0.1)
    win32api.keybd_event(ord('S'), 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

frame = win32gui.FindWindow("OrCaptureFrame", None)
rect = win32gui.GetWindowRect(frame)
win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
win32gui.BringWindowToTop(frame)
win32gui.SetWindowPos(frame, -1, 0,0,0,0, 0x0002|0x0001)
time.sleep(0.5)
# click blank canvas area
win32api.SetCursorPos((rect[0]+1200, rect[1]+700))
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0); time.sleep(0.1)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0); time.sleep(0.6)
print("foreground:", win32gui.GetForegroundWindow() == frame)
press_ctrl_s()
time.sleep(5)
st = os.stat(r"D:\Users\Download\exp3_BJT_CE\EXP3.DSN")
print("dsn mtime:", time.strftime("%H:%M:%S", time.localtime(st.st_mtime)), " now:", time.strftime("%H:%M:%S"))
print("dbk exists:", os.path.exists(r"D:\Users\Download\exp3_BJT_CE\EXP3_0.DBK"))
