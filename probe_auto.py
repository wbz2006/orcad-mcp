"""Probe 一体化自动化:加三条轨迹 + 打印为 PDF. 每步带前台断言."""
import sys, os, time
import win32gui, win32con, win32api, win32clipboard
from PIL import ImageGrab

PROBE_TITLE = "PSpice A/D Lite - [tran.dat]"
SHOTDIR = r"D:\Main_FIles\free-deng\orcad-mcp"

def fg_title():
    return win32gui.GetWindowText(win32gui.GetForegroundWindow())

def focus_probe():
    probe = win32gui.FindWindow(None, PROBE_TITLE)
    win32gui.SetWindowPos(probe, -1, 0, 0, 0, 0, 1)  # TOPMOST
    try: win32gui.SetForegroundWindow(probe)
    except Exception: pass
    time.sleep(0.8)
    ok = win32gui.GetForegroundWindow() == probe
    return probe, ok

def click(x, y):
    win32api.SetCursorPos((x, y))
    time.sleep(0.2)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.4)

def dblclick(x, y):
    click(x, y)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)

def shot(name):
    ImageGrab.grab().save(os.path.join(SHOTDIR, name))

def find_dialog():
    d = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "#32770" and ("Add Traces" in t or "Trace Expression" in t or True):
            # 找含 Trace Expression 标签的对话框
            kids = []
            win32gui.EnumChildWindows(h, lambda w, _: kids.append(win32gui.GetWindowText(w)) or True, None)
            kt = " ".join(kids)
            if "Trace Expression" in kt:
                d.append(h)
    win32gui.EnumWindows(cb, None)
    return d[0] if d else None

def main():
    probe, ok = focus_probe()
    print("focus:", ok, fg_title()[:40])
    if not ok:
        print("!! 无法前台化 Probe")
        return
    # 1) Trace 菜单(Probe 最大化, 2560 宽: Trace≈(324,48))
    r = win32gui.GetWindowRect(probe)
    click(r[0] + 324, r[1] + 48)
    time.sleep(1)
    shot("pa_menu.png")
    # 2) Add Traces... 是 Trace 菜单第 2 项(下拉菜单 y≈+30+22*1)
    click(r[0] + 400, r[1] + 100)
    time.sleep(1.5)
    dlg = find_dialog()
    print("dialog:", dlg)
    if not dlg:
        shot("pa_nodialog.png")
        print("!! Add Traces 对话框未出现——菜单项坐标需调整")
        return
    # 3) 枚举变量列表(ListBox)位置,双击 V(Vs)/V(Vi)/V(Vo)
    kids = []
    win32gui.EnumChildWindows(dlg, lambda w, _: kids.append((w, win32gui.GetClassName(w), win32gui.GetWindowText(w))) or True, None)
    lists = [w for w, c, t in kids if c in ("ListBox", "SysListView32")]
    print("lists:", lists)
    if not lists:
        print("!! no list")
        return
    lr = win32gui.GetWindowRect(lists[0])
    lx, ly = lr[0], lr[1]
    lh = lr[3] - lr[1]
    # 变量按字母序,35 个:V(Vo)/V(Vs)/V(Vi) 在列表后段。逐项扫描:双击每项,从列表底部往上找
    # 策略:直接双击列表底部往上 1/4 处的几个位置,匹配表达式框文本
    expr_edit = None
    for w, c, t in kids:
        if c == "Edit" and "Trace Expression" in win32gui.GetWindowText(win32gui.GetParent(w)):
            expr_edit = w
    if expr_edit is None:
        # 表达式框 = 最后一个 Edit
        edits = [w for w, c, t in kids if c == "Edit"]
        expr_edit = edits[-1] if edits else None
    print("expr edit:", expr_edit)

    def get_expr():
        buf = win32gui.PyMakeBuffer(512)
        L = win32gui.SendMessage(expr_edit, win32con.WM_GETTEXTLENGTH, 0, 0)
        win32gui.SendMessage(expr_edit, win32con.WM_GETTEXT, 512, buf)
        return buf[:L].tobytes().decode("utf-8", "ignore") if L else ""

    targets = ["V(Vs)", "V(Vi)", "V(Vo)"]
    # 列表滚动到 V 区:Home 后按 V 字母跳转?ListBox 支持 first-char 导航
    # 用双击扫描:从列表 y 从上往下 8 个位置逐个双击,读表达式框,匹配即停
    added = []
    for target in targets:
        found = False
        for frac in (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95):
            yy = int(lr[1] + lh * frac)
            dblclick(lx + 60, yy)
            time.sleep(0.25)
            e = get_expr()
            if target in e:
                found = True
                print(f"{target}: found at frac {frac}, expr={e!r}")
                # OK 按钮
                btns = [(w, t) for w, c, t in kids if c == "Button" and t == "OK"]
                if btns:
                    br_ = win32gui.GetWindowRect(btns[0][0])
                    click((br_[0] + br_[2]) // 2, (br_[1] + br_[3]) // 2)
                time.sleep(1.5)
                added.append(target)
                break
        if not found:
            print(f"!! {target} not found in list scan")
            # 关闭可能残留的对话框(ESC)
            win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
            win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.5)
            # 重新打开对话框
            click(r[0] + 324, r[1] + 48); time.sleep(1)
            click(r[0] + 400, r[1] + 100); time.sleep(1.5)
            dlg = find_dialog()
            if dlg:
                kids = []
                win32gui.EnumChildWindows(dlg, lambda w, _: kids.append((w, win32gui.GetClassName(w), win32gui.GetWindowText(w))) or True, None)
                lists = [w for w, c, t in kids if c in ("ListBox", "SysListView32")]
                if lists: lr = win32gui.GetWindowRect(lists[0])
    print("added:", added)
    shot("pa_traces.png")

    if len(added) == 3:
        # 4) File→Print:点击 File 菜单 (r[0]+20, r[1]+48) → Print...(下拉 y≈+190?)
        click(r[0] + 20, r[1] + 48)
        time.sleep(1)
        shot("pa_filemenu.png")
        # Print... 菜单项:File 菜单下拉里,位置待截图确认;先点 (r[0]+60, r[1]+190)
        click(r[0] + 60, r[1] + 190)
        time.sleep(1.5)
        shot("pa_printdlg.png")
        # 打印对话框:回车(默认 OK)
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(2.5)
        # 另存为对话框:枚举 #32770 含 Edit,填路径,点保存
        d2 = []
        def cb2(h, _):
            t = win32gui.GetWindowText(h)
            if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "#32770" and ("另存为" in t or "Save" in t):
                d2.append(h)
            return True
        win32gui.EnumWindows(cb2, d2)
        print("save-as:", d2)
        if d2:
            h = d2[0]
            edits = []
            win32gui.EnumChildWindows(h, lambda w, _: edits.append((w, win32gui.GetClassName(w))) or True, None)
            edits = [w for w, c in edits if c == "Edit"]
            if edits:
                win32clipboard.OpenClipboard(); win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(r"D:\Users\Download\exp3_BJT_CE\图3.4_IC2.5mA_Vi_VS_Vo波形_Probe导出.pdf", win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                win32gui.SendMessage(edits[0], win32con.WM_SETTEXT, 0, r"D:\Users\Download\exp3_BJT_CE\图3.4_IC2.5mA_Vi_VS_Vo波形_Probe导出.pdf")
                time.sleep(0.5)
                win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(3)
                print("PDF saved:", os.path.exists(r"D:\Users\Download\exp3_BJT_CE\图3.4_IC2.5mA_Vi_VS_Vo波形_Probe导出.pdf"))
    print("DONE")

main()
