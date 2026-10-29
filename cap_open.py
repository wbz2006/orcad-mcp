# -*- coding: utf-8 -*-
"""Open an OrCAD Capture project without foreground / mouse / keyboard.

Usage:
  python cap_open.py D:\\path\\project.opj

Starts Capture with ORCAD_MCP_PORT inherited (so the TCL agent connects to the
local bridge), answers startup dialogs by message, waits for the project title.
"""
import sys, os, time, subprocess
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
import print_export as pe

CAP = r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\Capture.exe"


def frames():
    out = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in win32gui.GetWindowText(h):
            out.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return out


def dialogs():
    out = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "#32770":
            out.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return out


def buttons(dlg):
    return [(w, win32gui.GetDlgCtrlID(w), pe.get_text(w))
            for w in pe.child_list(dlg) if win32gui.GetClassName(w) == "Button"]


def answer(dlg):
    bs = buttons(dlg)
    print("dialog:", repr(win32gui.GetWindowText(dlg)), [(i, t) for _, i, t in bs])
    for w, i, t in bs:
        if t.strip() in ("否(&N)", "否", "No"):
            win32gui.SendMessage(w, win32con.BM_CLICK, 0, 0)
            return
    for w, i, t in bs:
        if i == 1:
            win32gui.SendMessage(w, win32con.BM_CLICK, 0, 0)
            return
    if bs:
        win32gui.SendMessage(bs[0][0], win32con.BM_CLICK, 0, 0)


def main():
    opj = sys.argv[1]
    base = os.path.basename(opj)
    fs = frames()
    if not fs:
        env = dict(os.environ)
        env.setdefault("ORCAD_MCP_PORT", "5178")
        print("start Capture ...")
        subprocess.Popen([CAP, opj], env=env)
        t0 = time.time()
        while time.time() - t0 < 90 and not frames():
            time.sleep(1)
    fs = frames()
    assert fs, "Capture frame timeout"
    f = fs[0]
    print("frame", hex(f), win32gui.GetWindowText(f))

    t0 = time.time()
    while time.time() - t0 < 120:
        for d in dialogs():
            answer(d)
            time.sleep(1.2)
        t = win32gui.GetWindowText(f)
        if base.lower() in t.lower() or "SCHEMATIC1" in t:
            break
        time.sleep(1)
    print("title:", win32gui.GetWindowText(f))
    mdi = win32gui.FindWindowEx(f, 0, "MDIClient", None)
    act = win32gui.SendMessage(mdi, 0x0229, 0, 0) if mdi else 0
    print("active child:", repr(win32gui.GetWindowText(act) if act else ""))
    return 0 if (base.lower() in win32gui.GetWindowText(f).lower()
                 or "SCHEMATIC1" in win32gui.GetWindowText(f)) else 1


if __name__ == "__main__":
    sys.exit(main())
