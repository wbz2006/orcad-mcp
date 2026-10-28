# -*- coding: utf-8 -*-
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con, win32api, win32clipboard

DSN = r"D:\Users\Download\exp3_BJT_CE\EXP3.DSN"
frame = win32gui.FindWindow("OrCaptureFrame", None)


def find_dlg(title="Save As"):
    return win32gui.FindWindow("#32770", title)


def set_clip(txt):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(txt, win32clipboard.CF_UNICODETEXT)
    win32clipboard.CloseClipboard()


def ctrl_s():
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0); time.sleep(0.06)
    win32api.keybd_event(ord("S"), 0, 0, 0); time.sleep(0.1)
    win32api.keybd_event(ord("S"), 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.06)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)


win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE)
time.sleep(0.3)
win32gui.SetForegroundWindow(frame)
time.sleep(0.5)
print("fg", hex(win32gui.GetForegroundWindow()), "==", hex(frame))
before = os.stat(DSN).st_mtime
for attempt in range(3):
    ctrl_s()
    t0 = time.time()
    while time.time() - t0 < 12:
        time.sleep(0.5)
        if os.stat(DSN).st_mtime != before:
            print("SAVED %.1fs size=%d %s" % (time.time() - t0, os.stat(DSN).st_size,
                                              time.strftime("%H:%M:%S", time.localtime(os.stat(DSN).st_mtime))))
            sys.exit(0)
        dlg = find_dlg()
        if dlg:
            print("Save As dialog appeared -> fill EXP3.DSN")
            combo = win32gui.FindWindowEx(dlg, 0, "ComboBoxEx32", None)
            edit = win32gui.FindWindowEx(combo, 0, "Edit", None) if combo else 0
            win32gui.SetForegroundWindow(dlg)
            set_clip(DSN)
            win32gui.SetFocus(edit)
            time.sleep(0.2)
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0); time.sleep(0.05)
            win32api.keybd_event(ord("A"), 0, 0, 0); time.sleep(0.08)
            win32api.keybd_event(ord("A"), 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.05)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.15)
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0); time.sleep(0.05)
            win32api.keybd_event(ord("V"), 0, 0, 0); time.sleep(0.08)
            win32api.keybd_event(ord("V"), 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.05)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.3)
            print("field:", win32gui.GetWindowText(edit))
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0); time.sleep(0.08)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(1.5)
            # overwrite confirm
            if find_dlg("Save As"):
                win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0); time.sleep(0.08)
                win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(1.5)
            break
    print("attempt %d: no mtime change" % (attempt + 1))
    win32gui.SetForegroundWindow(frame)
    time.sleep(0.5)
print("SAVE FAILED")
