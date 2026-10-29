# -*- coding: utf-8 -*-
"""Quiet print-to-PDF for Capture / PSpice A/D / Probe: message-only.

Usage:
  python quiet_print.py <window-title-prefix> <out.pdf>

No SetForegroundWindow, no mouse, no keyboard. The target window must already
show the document to print (Capture: PAGE1 active; PSpice: bias.out / tran.dat
in its own MDI child).
"""
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con, win32print
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
import print_export as pe
import orcad_quiet as oq


def find_by_prefix(prefix):
    res = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and t.startswith(prefix):
            res.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return res[0] if res else None


def quiet_print(h, out, tag=""):
    win32print.SetDefaultPrinter("Microsoft Print to PDF")
    if os.path.exists(out):
        os.remove(out)
    assert pe.menu_cmd(h, "File", "Print"), "File>Print menu not found"
    d = pe.find_dlg(pe.is_print_dlg, 10)
    assert d, "print dialog not found"
    assert oq.bg_ok(d), "no default button in print dialog"
    time.sleep(1.0)
    d2 = pe.find_dlg(pe.is_saveas_dlg, 15)
    assert d2, "save-as dialog not found"
    e = next(w for w in pe.child_list(d2)
             if win32gui.GetClassName(w) == "Edit" and win32gui.IsWindowVisible(w))
    win32gui.SendMessage(e, win32con.WM_SETTEXT, 0, out)
    time.sleep(0.4)
    win32gui.SendMessage(d2, win32con.WM_COMMAND, win32con.IDOK, 0)
    t0 = time.time()
    while time.time() - t0 < 20:
        if os.path.exists(out) and os.path.getsize(out) > 500:
            break
        time.sleep(0.4)
        oq.dismiss_dialogs(overwrite_yes=True)
    ok = os.path.exists(out)
    print(f"[{tag}] pdf={ok}", os.path.getsize(out) if ok else 0)
    return ok


if __name__ == "__main__":
    prefix = sys.argv[1]
    out = sys.argv[2]
    h = find_by_prefix(prefix)
    assert h, f"window not found: {prefix}"
    print("window", hex(h), repr(win32gui.GetWindowText(h)))
    sys.exit(0 if quiet_print(h, out, prefix) else 1)
