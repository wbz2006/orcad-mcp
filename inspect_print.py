# -*- coding: utf-8 -*-
import sys, time
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
import win32gui, win32con, win32print
import print_export as pe

f = win32gui.FindWindow("OrCaptureFrame", None)
print("frame", hex(f), win32gui.GetWindowText(f))
win32print.SetDefaultPrinter("Microsoft Print to PDF")
print("menu", pe.menu_cmd(f, "File", "Print"))
d = pe.find_dlg(pe.is_print_dlg, 10)
print("dialog", hex(d) if d else None, win32gui.GetWindowText(d) if d else "")
if d:
    for w in pe.child_list(d):
        c = win32gui.GetClassName(w)
        t = pe.get_text(w)
        rid = win32gui.GetDlgCtrlID(w)
        st = ""
        try:
            st = "check=%d" % win32gui.SendMessage(w, win32con.BM_GETCHECK, 0, 0)
        except Exception:
            pass
        print(hex(w), c, rid, st, "|", repr(t)[:120])
    for w in pe.child_list(d):
        if win32gui.GetClassName(w) == "Button":
            t = pe.get_text(w)
            if ("取消" in t) or ("Cancel" in t):
                print("cancel", hex(w))
                win32gui.SendMessage(w, win32con.BM_CLICK, 0, 0)
                break
