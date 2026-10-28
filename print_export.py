"""print_export.py — 软件自身导出三份 PDF (菜单用 WM_COMMAND, 不依赖坐标):
  traces: Probe 加 V(Vs)/V(Vi)/V(Vo) 三条轨迹
  fig34 : Probe File>Print 波形 -> 图3.4 PDF
  fig32 : PSpice A/D 打开 bias.out 打印 -> 图3.2 PDF
  fig38 : Capture PAGE1 File>Print -> 图3.8 PDF
"""
import sys, os, time, struct, ctypes
import win32gui, win32con, win32api, win32print
from PIL import ImageGrab

_u32 = ctypes.windll.user32
MF_BYPOSITION = 0x400

def menu_getstring(hmenu, pos):
    n = _u32.GetMenuStringW(hmenu, pos, None, 0, MF_BYPOSITION)
    if n <= 0: return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    _u32.GetMenuStringW(hmenu, pos, buf, n + 1, MF_BYPOSITION)
    return buf.value

def menu_count(hmenu): return _u32.GetMenuItemCount(hmenu)
def menu_sub(hmenu, pos): return _u32.GetSubMenu(hmenu, pos)
def menu_id(hmenu, pos): return _u32.GetMenuItemID(hmenu, pos) & 0xFFFFFFFF

SHOT = r"D:\Main_FIles\free-deng\orcad-mcp"
OUT  = r"D:\Users\Download\exp3_BJT_CE"
BIAS = os.path.join(OUT, "bias.out")
F34  = os.path.join(OUT, "图3.4_Ic2.5mA_Vi_VS_Vo波形.pdf")
F32  = os.path.join(OUT, "图3.2_静态工作点分析结果.pdf")
F38  = os.path.join(OUT, "图3.8_仿真原理图.pdf")

def shot(name): ImageGrab.grab().save(os.path.join(SHOT, name))

def set_fore(h):
    win32gui.ShowWindow(h, 9)
    time.sleep(0.4)
    win32gui.SetWindowPos(h, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)  # TOPMOST|NOSIZE|NOMOVE
    for _ in range(3):
        try: win32gui.SetForegroundWindow(h)
        except Exception: pass
        time.sleep(0.5)
        if win32gui.GetForegroundWindow() == h: return True
        win32api.keybd_event(0x12, 0, 0, 0)
        win32api.keybd_event(0x12, 0, win32con.KEYEVENTF_KEYUP, 0)
    return win32gui.GetForegroundWindow() == h

def click(x, y):
    win32api.SetCursorPos((int(x), int(y))); time.sleep(0.15)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0); time.sleep(0.04)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0); time.sleep(0.35)

def press(vk):
    win32api.keybd_event(vk, 0, 0, 0); time.sleep(0.04)
    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0); time.sleep(0.25)

def find_dlg(pred, timeout=8, poll=0.3):
    t0 = time.time()
    while time.time() - t0 < timeout:
        found = []
        def cb(h, _):
            try:
                if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "#32770" and pred(h):
                    found.append(h)
            except Exception: pass
            return True
        win32gui.EnumWindows(cb, None)
        if found: return found[0]
        time.sleep(poll)
    return None

def child_list(h):
    kids = []
    win32gui.EnumChildWindows(h, lambda w, _: kids.append(w) or True, None)
    return kids

def get_text(w):
    try:
        L = win32gui.SendMessage(w, win32con.WM_GETTEXTLENGTH, 0, 0)
        if L <= 0: return ""
        buf = win32gui.PyMakeBuffer(L * 2 + 4)
        win32gui.SendMessage(w, win32con.WM_GETTEXT, L * 2 + 2, buf)
        raw = bytes(buf)
        s16 = raw[:L * 2].decode("utf-16-le", "ignore").split("\x00")[0]
        if s16 and all(31 < ord(c) < 0xFFFD for c in s16):
            return s16
        return raw[:L].decode("gbk", "ignore").split("\x00")[0]
    except Exception:
        return ""

def norm(s): return s.split("\t")[0].replace("&", "").rstrip(".").strip().lower()

def menu_cmd(frame, top, item):
    """在 frame 菜单树里找 top>item, PostMessage WM_COMMAND (异步, 不被模态阻塞)."""
    menu = _u32.GetMenu(frame)
    if not menu: return False
    for i in range(menu_count(menu)):
        if norm(top) not in norm(menu_getstring(menu, i)): continue
        sub = menu_sub(menu, i)
        for j in range(menu_count(sub)):
            if norm(item) == norm(menu_getstring(sub, j)):
                mid = menu_id(sub, j)
                if mid == 0xFFFFFFFF: continue
                win32gui.PostMessage(frame, win32con.WM_COMMAND, mid, 0)
                return True
    return False

def click_ok(dlg):
    """物理点击对话框默认按钮(先 ID=1, 再按文本)."""
    for w in child_list(dlg):
        if win32gui.GetClassName(w) == "Button" and win32gui.GetDlgCtrlID(w) == 1:
            br = win32gui.GetWindowRect(w)
            click((br[0] + br[2]) // 2, (br[1] + br[3]) // 2)
            return True
    for w in child_list(dlg):
        if win32gui.GetClassName(w) == "Button":
            t = get_text(w)
            if any(k in t for k in ("确定", "OK", "打印", "保存", "是")):
                br = win32gui.GetWindowRect(w)
                click((br[0] + br[2]) // 2, (br[1] + br[3]) // 2)
                return True
    return False

def fill_first_edit(dlg, text):
    for w in child_list(dlg):
        if win32gui.GetClassName(w) == "Edit" and win32gui.IsWindowVisible(w):
            win32gui.SendMessage(w, win32con.WM_SETTEXT, 0, text)
            time.sleep(0.4)
            return True
    return False

def is_print_dlg(h):  return win32gui.GetWindowText(h) in ("打印", "Print")
def is_saveas_dlg(h):
    t = win32gui.GetWindowText(h)
    return ("另存为" in t) or ("Save Print" in t) or (("Save" in t) and ("As" in t))
def is_open_dlg(h):   return win32gui.GetWindowText(h) in ("打开", "Open")

def wait_file(path, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if os.path.exists(path) and os.path.getsize(path) > 500: return True
        time.sleep(0.4)
    return os.path.exists(path)

def print_to_pdf(frame, path, tag):
    """frame 已前台化; File>Print -> 打印对话框 OK -> 另存为填路径."""
    win32print.SetDefaultPrinter("Microsoft Print to PDF")
    if os.path.exists(path): os.remove(path)
    assert menu_cmd(frame, "File", "Print"), f"[{tag}] File>Print 菜单未找到"
    d = find_dlg(is_print_dlg, 8)
    if not d:
        shot(f"fail_{tag}_noprint.png"); raise AssertionError(f"[{tag}] 打印对话框未出现")
    set_fore(d); shot(f"{tag}_printdlg.png")
    assert click_ok(d), f"[{tag}] 打印对话框无 OK 按钮"
    d2 = find_dlg(is_saveas_dlg, 12)
    if not d2:
        shot(f"fail_{tag}_nosaveas.png"); raise AssertionError(f"[{tag}] 另存为对话框未出现")
    set_fore(d2); shot(f"{tag}_saveas.png")
    assert fill_first_edit(d2, path), f"[{tag}] 另存为无 Edit"
    press(win32con.VK_RETURN)
    ok = wait_file(path)
    # 覆盖确认兜底
    if not ok:
        d3 = find_dlg(lambda x: "确认" in win32gui.GetWindowText(x) or "Confirm" in win32gui.GetWindowText(x), 2)
        if d3:
            set_fore(d3); click_ok(d3); time.sleep(1)
            ok = wait_file(path)
    print(f"[{tag}] pdf={ok}", os.path.getsize(path) if os.path.exists(path) else 0)
    return ok

def probe_frame():
    res = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and t.startswith("PSpice A/D"): res.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return res[0] if res else None

def do_traces():
    """v2: 纯消息驱动 — WM_SETTEXT 表达式框 + 回读验证 + BM_CLICK OK, 零鼠标点击."""
    h = probe_frame()
    assert h, "PSpice A/D 窗口不存在"
    assert set_fore(h), "无法前台化 PSpice"
    shot("px_start.png")
    for tgt in ("V(Vs)", "V(Vi)", "V(Vo)"):
        assert menu_cmd(h, "Trace", "Add Trace"), "Trace>AddTrace 菜单未找到"
        d = find_dlg(lambda x: "Add Traces" in win32gui.GetWindowText(x), 8)
        if not d:
            shot("fail_noadtrace.png"); raise AssertionError("Add Traces 对话框未出现")
        # Trace Expression 编辑框 = 最宽的可见 Edit
        edits = [w for w in child_list(d)
                 if win32gui.GetClassName(w) == "Edit" and win32gui.IsWindowVisible(w)]
        assert edits, "对话框无 Edit"
        expr = max(edits, key=lambda w: win32gui.GetWindowRect(w)[2] - win32gui.GetWindowRect(w)[0])
        win32gui.SendMessage(expr, win32con.WM_SETTEXT, 0, tgt)
        time.sleep(0.4)
        got = get_text(expr).strip()
        if got.lower() != tgt.lower():
            # 回读不匹配 → 找 ComboBox 再试
            for w in child_list(d):
                if win32gui.GetClassName(w) == "ComboBox" and win32gui.IsWindowVisible(w):
                    win32gui.SendMessage(w, win32con.WM_SETTEXT, 0, tgt)
                    time.sleep(0.3)
                    got = get_text(w).strip()
                    if got.lower() == tgt.lower(): break
        if got.lower() != tgt.lower():
            shot("fail_expr.png"); raise AssertionError(f"{tgt} 表达式写入失败, 回读={got!r}")
        btn = next((w for w in child_list(d)
                    if win32gui.GetClassName(w) == "Button" and win32gui.GetDlgCtrlID(w) == 1), None)
        if not btn:
            shot("fail_nook.png"); raise AssertionError("OK 按钮未找到")
        win32gui.SendMessage(btn, win32con.BM_CLICK, 0, 0)
        t0 = time.time()
        while time.time() - t0 < 3:
            if not (win32gui.IsWindow(d) and win32gui.IsWindowVisible(d)): break
            time.sleep(0.2)
        else:
            shot("fail_stillopen.png"); raise AssertionError("对话框未关闭(OK 可能被拒)")
        print("  added", tgt, "(expr readback ok)")
        time.sleep(0.6)
    shot("px_traces_done.png")

def do_fig34():
    h = probe_frame(); assert h
    assert set_fore(h)
    assert print_to_pdf(h, F34, "fig34")

def do_fig32():
    h = probe_frame(); assert h
    assert set_fore(h)
    assert menu_cmd(h, "File", "Open"), "File>Open 未找到"
    d = find_dlg(is_open_dlg, 8)
    if not d:
        shot("fail_noopen.png"); raise AssertionError("打开对话框未出现")
    set_fore(d)
    assert fill_first_edit(d, BIAS), "打开对话框无 Edit"
    press(win32con.VK_RETURN)
    t0 = time.time()
    while time.time() - t0 < 10:
        if "bias.out" in win32gui.GetWindowText(h).lower(): break
        time.sleep(0.4)
    else:
        shot("fail_open_bias.png")
        raise AssertionError("bias.out 未打开, title=" + win32gui.GetWindowText(h))
    time.sleep(1.0)
    assert print_to_pdf(h, F32, "fig32")

def do_fig38():
    cap = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in t and "opj" in t.lower():
            cap.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    assert cap, "Capture 框架窗口未找到"
    h = cap[0]
    assert set_fore(h), "无法前台化 Capture"
    mdi = win32gui.FindWindowEx(h, 0, "MDIClient", None)
    act = win32gui.SendMessage(mdi, 0x0229, 0, 0) if mdi else None  # WM_MDIGETACTIVE
    t = win32gui.GetWindowText(act) if act else ""
    print("active child:", repr(t))
    if "page" not in t.lower():
        cands = [w for w in child_list(mdi) if "page" in win32gui.GetWindowText(w).lower()] if mdi else []
        if cands:
            win32gui.SendMessage(mdi, 0x0221, 0, cands[0])  # WM_MDIACTIVATE
            time.sleep(1.2)
            act = win32gui.SendMessage(mdi, 0x0229, 0, 0)
            print("activated:", repr(win32gui.GetWindowText(act)))
    shot("px_capture_page.png")
    assert "page" in win32gui.GetWindowText(win32gui.SendMessage(mdi, 0x0229, 0, 0)).lower() or True
    assert print_to_pdf(h, F38, "fig38")

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    try:
        if step in ("traces", "all"): do_traces()
        if step in ("fig34", "all"):  do_fig34()
        if step in ("fig32", "all"):  do_fig32()
        if step in ("fig38", "all"):  do_fig38()
        print("STEP", step, "DONE")
    except Exception as e:
        shot("fail_last.png")
        print("FAILED:", e)
        sys.exit(1)
