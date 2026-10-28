# -*- coding: utf-8 -*-
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui, win32con, win32api, win32clipboard

DSN = r"D:\Users\Download\exp3_BJT_CE\EXP3.DSN"

def find_dlg(title="Save As"):
    return win32gui.FindWindow("#32770", title)

def set_clip(txt):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(txt, win32clipboard.CF_UNICODETEXT)
    win32clipboard.CloseClipboard()

frame = win32gui.FindWindow("OrCaptureFrame", None)
win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
win32gui.SetForegroundWindow(frame)
time.sleep(0.4)
before = os.stat(DSN).st_mtime
win32api.keybd_event(win32con.VK_CONTROL,0,0,0); time.sleep(0.05)
win32api.keybd_event(ord("S"),0,0,0); time.sleep(0.1)
win32api.keybd_event(ord("S"),0,win32con.KEYEVENTF_KEYUP,0); time.sleep(0.05)
win32api.keybd_event(win32con.VK_CONTROL,0,win32con.KEYEVENTF_KEYUP,0)
time.sleep(2)
dlg = find_dlg()
print("dialog:", dlg)
if not dlg:
    print("no dialog; wait mtime")
    t0=time.time()
    while time.time()-t0<20:
        time.sleep(0.5)
        if os.stat(DSN).st_mtime != before:
            print("SAVED direct"); sys.exit(0)
    print("no save, no dialog"); sys.exit(1)

# focus filename edit: find first Edit child of ComboBoxEx32
combo = win32gui.FindWindowEx(dlg, 0, "ComboBoxEx32", None)
edit = win32gui.FindWindowEx(combo, 0, "Edit", None) if combo else 0
if not edit:
    edit = win32gui.FindWindowEx(dlg, 0, "Edit", None)
print("combo", combo, "edit", edit)
win32gui.SetForegroundWindow(dlg)
set_clip(DSN)
win32gui.SetFocus(edit)
time.sleep(0.2)
win32api.keybd_event(win32con.VK_CONTROL,0,0,0); time.sleep(0.05)
win32api.keybd_event(ord("A"),0,0,0); time.sleep(0.08)
win32api.keybd_event(ord("A"),0,win32con.KEYEVENTF_KEYUP,0); time.sleep(0.05)
win32api.keybd_event(win32con.VK_CONTROL,0,win32con.KEYEVENTF_KEYUP,0); time.sleep(0.2)
win32api.keybd_event(win32con.VK_CONTROL,0,0,0); time.sleep(0.05)
win32api.keybd_event(ord("V"),0,0,0); time.sleep(0.08)
win32api.keybd_event(ord("V"),0,win32con.KEYEVENTF_KEYUP,0); time.sleep(0.05)
win32api.keybd_event(win32con.VK_CONTROL,0,win32con.KEYEVENTF_KEYUP,0); time.sleep(0.4)
buf = win32gui.GetWindowText(edit)
print("field now:", buf)
win32api.keybd_event(win32con.VK_RETURN,0,0,0); time.sleep(0.08)
win32api.keybd_event(win32con.VK_RETURN,0,win32con.KEYEVENTF_KEYUP,0)
time.sleep(2)
# possible overwrite confirm
for _ in range(10):
    if not find_dlg("Save As"):
        break
    # find a Yes button and press Enter
    win32api.keybd_event(win32con.VK_RETURN,0,0,0); time.sleep(0.08)
    win32api.keybd_event(win32con.VK_RETURN,0,win32con.KEYEVENTF_KEYUP,0)
    time.sleep(1.5)
t0=time.time()
while time.time()-t0<30:
    time.sleep(0.5)
    if os.stat(DSN).st_mtime != before:
        print("SAVED %.1fs size=%d %s" % (time.time()-t0, os.stat(DSN).st_size, time.strftime("%H:%M:%S", time.localtime(os.stat(DSN).st_mtime))))
        sys.exit(0)
print("STILL NOT SAVED; dlg=", find_dlg("Save As"), "title=", win32gui.GetWindowText(win32gui.GetForegroundWindow()))
