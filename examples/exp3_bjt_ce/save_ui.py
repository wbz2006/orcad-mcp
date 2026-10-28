# -*- coding: utf-8 -*-
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui, win32con, win32api

DSN = r"D:\Users\Download\exp3_BJT_CE\EXP3.DSN"

def focus():
    frame = win32gui.FindWindow("OrCaptureFrame", None)
    rect = win32gui.GetWindowRect(frame)
    win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
    win32gui.BringWindowToTop(frame)
    win32gui.SetWindowPos(frame, -1, 0,0,0,0, 0x0002|0x0001)
    time.sleep(0.4)
    if win32gui.GetForegroundWindow() != frame:
        win32api.SetCursorPos((rect[0]+1200, rect[1]+700))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0); time.sleep(0.1)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0); time.sleep(0.5)
    return frame, rect

def press_ctrl_s():
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0); time.sleep(0.05)
    win32api.keybd_event(ord('S'), 0, 0, 0); time.sleep(0.1)
    win32api.keybd_event(ord('S'), 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.05)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)

before = os.stat(DSN).st_mtime
frame, rect = focus()
win32api.SetCursorPos((rect[0]+1200, rect[1]+700))
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0); time.sleep(0.1)
win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0); time.sleep(0.5)
for attempt in range(3):
    press_ctrl_s()
    t0 = time.time()
    while time.time() - t0 < 25:
        time.sleep(1)
        if os.stat(DSN).st_mtime != before:
            print("saved after %.0fs (attempt %d), size=%d, %s" % (time.time()-t0, attempt+1, os.stat(DSN).st_size, time.strftime("%H:%M:%S", time.localtime(os.stat(DSN).st_mtime))))
            sys.exit(0)
    print("attempt %d: no mtime change" % (attempt+1))
print("SAVE FAILED")
