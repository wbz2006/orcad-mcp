"""probe_fig318.py — 按手册图3.18 重构 Probe:上坐标系 Vo,下坐标系 Vi+Vs"""
import time, win32gui, win32con
import print_export as pe

def add_trace(h, tgt):
    assert pe.menu_cmd(h, "Trace", "Add Trace"), "Add Trace menu"
    d = pe.find_dlg(lambda x: "Add Traces" in win32gui.GetWindowText(x), 8)
    assert d, "Add Traces dlg"
    edits = [w for w in pe.child_list(d)
             if win32gui.GetClassName(w) == "Edit" and win32gui.IsWindowVisible(w)]
    expr = max(edits, key=lambda w: win32gui.GetWindowRect(w)[2] - win32gui.GetWindowRect(w)[0])
    win32gui.SendMessage(expr, win32con.WM_SETTEXT, 0, tgt)
    time.sleep(0.4)
    got = pe.get_text(expr).strip()
    assert got.lower() == tgt.lower(), f"expr readback {got!r}"
    btn = next((w for w in pe.child_list(d)
                if win32gui.GetClassName(w) == "Button" and win32gui.GetDlgCtrlID(w) == 1), None)
    win32gui.SendMessage(btn, win32con.BM_CLICK, 0, 0)
    t0 = time.time()
    while time.time() - t0 < 3:
        if not (win32gui.IsWindow(d) and win32gui.IsWindowVisible(d)): break
        time.sleep(0.2)
    else:
        raise AssertionError("dlg not closed")
    print("  added", tgt)

def main():
    h = pe.probe_frame()
    pe.set_fore(h)
    # 切到 tran.dat 标签 (实测 actual (58,420))
    pe.click(58, 420)
    time.sleep(1.2)
    t = win32gui.GetWindowText(h)
    print("after tab click:", t)
    if "tran.dat" not in t:
        pe.click(50, 419); time.sleep(1.2)
        t = win32gui.GetWindowText(h); print("retry:", t)
    assert "tran.dat" in t, "tran.dat 未激活"
    win32gui.ShowWindow(h, 3)  # maximize
    time.sleep(1.0)
    pe.set_fore(h)
    # 清空轨迹
    assert pe.menu_cmd(h, "Trace", "Delete All Traces"), "delete all"
    time.sleep(1.0)
    pe.shot("pf_cleared.png")
    # 下坐标系: Vs + Vi
    add_trace(h, "V(Vs)")
    add_trace(h, "V(Vi)")
    # 新坐标系(顶部) + Vo
    assert pe.menu_cmd(h, "Plot", "Add Plot to Window"), "add plot"
    time.sleep(1.0)
    add_trace(h, "V(Vo)")
    time.sleep(1.0)
    pe.shot("pf_fig318.png")
    print("layout done")

if __name__ == "__main__":
    main()
