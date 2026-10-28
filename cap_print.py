"""cap_print.py — 重启 Capture → 恢复对话框 → 物理点击 PAGE1 标签 → 打印原理图 PDF"""
import os, subprocess, time, struct, ctypes, win32gui, win32con
import print_export as pe
from PIL import ImageGrab

u32 = ctypes.windll.user32
SMTO_ABORTIFHUNG = 2
CAP_EXE = r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\Capture.exe"
OPJ = r"D:\Users\Download\exp3_BJT_CE\exp3.opj"

def sendmsgto(h, msg, wp, lp, timeout=3000):
    res = ctypes.c_ulong(0)
    ok = u32.SendMessageTimeoutW(h, msg, wp, lp, SMTO_ABORTIFHUNG, timeout, ctypes.byref(res))
    return (res.value if ok else None)

def top_dlg():
    out = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "#32770":
            out.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return out

def click_id(dlg, ident):
    for w in pe.child_list(dlg):
        if win32gui.GetClassName(w) == "Button" and win32gui.GetDlgCtrlID(w) == ident:
            win32gui.SendMessage(w, win32con.BM_CLICK, 0, 0)
            return True
    return False

def main():
    # 已有实例则直接用, 否则启动
    frame = None
    def cb(h, _):
        nonlocal frame
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in t:
            frame = frame or h
        return True
    win32gui.EnumWindows(cb, None)
    if not frame:
        subprocess.Popen([CAP_EXE, OPJ])
        t0 = time.time()
        while time.time() - t0 < 60 and not frame:
            win32gui.EnumWindows(cb, None)
            time.sleep(1)
        assert frame, "Capture frame timeout"
    print("frame:", frame, win32gui.GetWindowText(frame)[:60])
    pe.set_fore(frame)
    # 处理启动期对话框(恢复/提示): 点确定(id=1), 最多 4 轮
    for _ in range(4):
        ds = top_dlg()
        if not ds: break
        for d in ds:
            print("startup dialog:", win32gui.GetWindowText(d)[:50])
            if not click_id(d, 1):
                print("  no IDOK, try IDCANCEL"); click_id(d, 2)
            time.sleep(1.5)
    # 等工程加载
    t0 = time.time()
    while time.time() - t0 < 90:
        if "exp3.opj" in win32gui.GetWindowText(frame): break
        time.sleep(1)
    print("title:", win32gui.GetWindowText(frame)[:70])
    assert "exp3.opj" in win32gui.GetWindowText(frame), "项目未加载"
    time.sleep(2)
    mdi = win32gui.FindWindowEx(frame, 0, "MDIClient", None)
    act = sendmsgto(mdi, 0x0229, 0, 0)
    print("active child:", win32gui.GetWindowText(act) if act else None)
    if act and "SCHEMATIC1" not in win32gui.GetWindowText(act):
        # 物理点击 PAGE1 标签(实测屏幕坐标: 标签条 y≈129, PAGE1 x≈72-120)
        pe.set_fore(frame)
        ImageGrab.grab().save(os.path.join(pe.SHOT, "px_pre_tab.png"))
        pe.click(96, 129)
        time.sleep(1.5)
        act = sendmsgto(mdi, 0x0229, 0, 0)
        print("after tab click:", win32gui.GetWindowText(act) if act else None)
    ImageGrab.grab().save(os.path.join(pe.SHOT, "px_page_active.png"))
    assert act and "SCHEMATIC1" in win32gui.GetWindowText(act), "PAGE1 未激活"
    assert pe.print_to_pdf(frame, pe.F38, "fig38")

if __name__ == "__main__":
    main()
    print("DONE")
