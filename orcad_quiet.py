"""orcad_quiet.py — 后台安静模式:全程不抢焦点、不置顶、不模拟键盘鼠标。
原理:所有交互走窗口消息(PostMessage/SendMessage)——菜单命令、BM_CLICK、
WM_SETTEXT、LB_SETSEL、WM_LBUTTONDOWN(标注放置)。
前台只做一件事:枚举窗口。用户可同时正常使用电脑。
"""
import os, time, win32gui, win32con
import print_export as pe

MENU_LABEL_TEXT = 0x802e          # Probe Plot>Label>Text
LB_SETSEL       = 0x0185
LB_GETCOUNT     = 0x018B
LB_GETTEXTLEN   = 0x018A
LB_GETTEXT      = 0x0189


def bg_click(hwnd, lparam):
    """给窗口发一次鼠标按下+抬起(后台, 不动真实光标)。"""
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
    time.sleep(0.06)
    win32gui.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)


def bg_ok(dlg):
    """对话框默认按钮(确定/OK/保存)走 BM_CLICK 消息。"""
    for w in pe.child_list(dlg):
        if win32gui.GetClassName(w) == 'Button' and win32gui.GetDlgCtrlID(w) == 1:
            win32gui.SendMessage(w, win32con.BM_CLICK, 0, 0)
            return True
    for w in pe.child_list(dlg):
        if win32gui.GetClassName(w) == 'Button':
            t = pe.get_text(w)
            if any(k in t for k in ('确定', 'OK', '保存', '打印', '是')):
                win32gui.SendMessage(w, win32con.BM_CLICK, 0, 0)
                return True
    return False


def bg_click_text(dlg, *prefixes):
    """按按钮文本前缀点击(处理 ctrl id=0 的非标准对话框)。"""
    for w in pe.child_list(dlg):
        if win32gui.GetClassName(w) == 'Button':
            t = pe.get_text(w)
            if any(t.startswith(p) for p in prefixes):
                win32gui.SendMessage(w, win32con.BM_CLICK, 0, 0)
                return True
    return False


def dismiss_dialogs(overwrite_yes=True):
    """清扫所有可见模态框:覆盖确认(是/确定)、保存提示(否)、崩溃报告(Close)。
    返回清掉的个数。"""
    n = 0
    for _ in range(6):
        dlg = []
        def cb(h, _):
            if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == '#32770':
                dlg.append(h)
            return True
        win32gui.EnumWindows(cb, None)
        if not dlg: break
        for d in dlg:
            title = win32gui.GetWindowText(d)
            kids = [(win32gui.GetDlgCtrlID(w), w, pe.get_text(w))
                    for w in pe.child_list(d) if win32gui.GetClassName(w) == 'Button']
            done = False
            if '确认另存为' in title or 'Confirm Save As' in title:
                # 是(&Y) / 确定
                done = bg_click_text(d, '是', '确定') or bg_ok(d)
            elif '另存为' in title or 'Save As' in title or 'Save Print' in title:
                continue  # 交给上层处理
            elif 'quit unexpectedly' in ' '.join(t for _, _, t in kids):
                done = bg_click_text(d, '&Close', 'Close', '关闭')
            elif 'ORCAP' in ' '.join(t for _, _, t in kids) or 'PSpice' == title:
                # 保存更改提示: 否;其他: 确定
                done = bg_click_text(d, '否') or bg_ok(d)
            else:
                done = bg_ok(d)
            n += 1
            time.sleep(1.2)
    return n


def probe_frame():
    res = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and t.startswith('PSpice A/D'):
            res.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return res[0] if res else None


def plot_view(frame):
    """Probe 绘图区子窗口 = 面积最大的 Afx 视图。"""
    best, bestA = None, 0
    def cb(w, _):
        nonlocal best, bestA
        c = win32gui.GetClassName(w)
        if c.startswith('Afx'):
            l, t, r, b = win32gui.GetWindowRect(w)
            a = max(0, r - l) * max(0, b - t)
            if a > bestA and (r - l) > 300 and (b - t) > 200:
                best, bestA = w, a
        return True
    win32gui.EnumChildWindows(frame, cb, None)
    return best


def lb_select(lb, index):
    win32gui.SendMessage(lb, LB_SETSEL, 1, index)
    parent = win32gui.GetParent(lb)
    win32gui.SendMessage(parent, win32con.WM_COMMAND, (1 << 16) | 1130, lb)


def lb_pick_by_text(lb, want):
    cnt = win32gui.SendMessage(lb, LB_GETCOUNT, 0, 0)
    pick = 0
    for i in range(cnt):
        ln = win32gui.SendMessage(lb, LB_GETTEXTLEN, i, 0)
        buf = win32gui.PyMakeBuffer(ln * 2 + 8)
        win32gui.SendMessage(lb, LB_GETTEXT, i, buf)
        s = bytes(buf)[:ln * 2].decode('utf-16-le', 'ignore').split('\x00')[0]
        if want in s:
            pick = i
    return pick


def wait_title(h, key, timeout=12):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if key in win32gui.GetWindowText(h).lower(): return True
        time.sleep(0.4)
    return False


def find_dlg(pred, timeout=8):
    return pe.find_dlg(pred, timeout)


# ---------- 高层流程 ----------

def quiet_open_dat(h, dat_path):
    name = os.path.basename(dat_path)
    pe.menu_cmd(h, 'File', 'Open')
    d = find_dlg(lambda x: win32gui.GetWindowText(x) in ('打开', 'Open'), 8)
    assert d, 'no open dialog'
    e = next(w for w in pe.child_list(d)
             if win32gui.GetClassName(w) == 'Edit' and win32gui.IsWindowVisible(w))
    win32gui.SendMessage(e, win32con.WM_SETTEXT, 0, dat_path)
    time.sleep(0.4)
    bg_ok(d)
    assert wait_title(h, name.lower()), 'dat not opened: ' + win32gui.GetWindowText(h)
    time.sleep(1.5)


def quiet_add_trace(h, expr):
    from probe_fig318 import add_trace  # 纯 PostMessage 实现, 后台安全
    add_trace(h, expr)


def quiet_two_frame(h, traces):
    for t in traces[:-1]: quiet_add_trace(h, t)
    pe.menu_cmd(h, 'Plot', 'Add Plot to Window')
    time.sleep(1.2)
    quiet_add_trace(h, traces[-1])
    time.sleep(0.8)


def quiet_label(h, text, view, place=(600, 300)):
    """标注: OK 后处于 move-mode, 放置点由真实光标位置决定(GetCursorPos)。
    安静模式: SetCursorPos 移动真实光标(不点击不抢焦点) + 消息点击放置,
    放完由调用方恢复用户光标。"""
    win32gui.PostMessage(h, win32con.WM_COMMAND, MENU_LABEL_TEXT, 0)
    d = find_dlg(lambda x: 'Label Text' in win32gui.GetWindowText(x), 8)
    assert d, 'no label dialog'
    e = next(w for w in pe.child_list(d) if win32gui.GetClassName(w) == 'Edit')
    win32gui.SendMessage(e, win32con.WM_SETTEXT, 0, text)
    time.sleep(0.3)
    bg_ok(d)
    time.sleep(1.2)
    # 客户坐标 -> 屏幕坐标, 移动真实光标
    import win32api
    sx, sy = win32gui.ClientToScreen(view, place)
    win32api.SetCursorPos((sx, sy))
    time.sleep(0.3)
    # 消息点击放置
    x, y = place
    lparam = (y << 16) | x
    bg_click(view, lparam)
    time.sleep(0.8)


def mdi_children(frame):
    kids = []
    k = None
    while True:
        k = win32gui.FindWindowEx(frame, k, 'MDIClient', None)
        if k: break
    if not k: return kids
    c = None
    while True:
        c = win32gui.FindWindowEx(k, c, None, None)
        if not c: break
        kids.append(c)
    return kids


def quiet_close_all_children(h, keep_title=None):
    """WM_CLOSE 关闭所有 MDI 子窗口(keep_title 除外);弹出保存提示自动点'否'。
    后台安全:纯消息。返回关闭数量。"""
    closed = 0
    for _ in range(8):
        kids = mdi_children(h)
        target = None
        for k in kids:
            t = win32gui.GetWindowText(k)
            if keep_title and keep_title in t: continue
            target = k; break
        if target is None: break
        win32gui.PostMessage(target, win32con.WM_CLOSE, 0, 0)
        time.sleep(1.0)
        # 保存提示? 点'否'
        d = find_dlg(lambda x: True, 1.5)
        if d:
            for w in pe.child_list(d):
                if win32gui.GetClassName(w) == 'Button':
                    t = pe.get_text(w)
                    if t.startswith('否') or t.startswith('N') or '(&N)' in t:
                        win32gui.SendMessage(w, win32con.BM_CLICK, 0, 0)
                        break
            else:
                bg_ok(d)
            time.sleep(0.8)
        if win32gui.IsWindow(target):  # 还在=被提示挡住, 再补一发否
            d = find_dlg(lambda x: True, 1.0)
            if d:
                for w in pe.child_list(d):
                    if win32gui.GetClassName(w) == 'Button':
                        t = pe.get_text(w)
                        if t.startswith('否') or '(&N)' in t:
                            win32gui.SendMessage(w, win32con.BM_CLICK, 0, 0)
                            break
                time.sleep(0.8)
        closed += 1
    return closed


def pdf_has(target, *keys):
    import pymupdf
    doc = pymupdf.open(target)
    t = doc[0].get_text()
    doc.close()
    # 中文 TTF 常把空格映射成 U+00A0;按"去空白"比较,避免标注核验误判
    flat = lambda s: ''.join(s.split())
    return all(flat(k) in flat(t) for k in keys)


def set_bw(dlg):
    """打印对话框 'Number of Trace Colors' 设 0 => 黑白前景(实验要求白底黑字)。"""
    e = next((w for w in pe.child_list(dlg)
              if win32gui.GetClassName(w) == 'Edit' and win32gui.GetDlgCtrlID(w) == 1162), None)
    if e:
        win32gui.SendMessage(e, win32con.WM_SETTEXT, 0, '0')
        time.sleep(0.2)
        return True
    return False


def quiet_print(h, target, want):
    if os.path.exists(target): os.remove(target)   # 防覆盖确认框
    pe.menu_cmd(h, 'File', 'Print')
    d = find_dlg(lambda x: win32gui.GetWindowText(x) in ('打印', 'Print'), 10)
    assert d, 'no print dialog'
    lb = next((w for w in pe.child_list(d) if win32gui.GetDlgCtrlID(w) == 1130), None)
    if lb:
        idx = lb_pick_by_text(lb, want)
        lb_select(lb, idx)
        time.sleep(0.3)
    set_bw(d)
    bg_ok(d)
    time.sleep(0.8)
    d2 = find_dlg(pe.is_saveas_dlg, 12)
    assert d2, 'no save-as'
    e = next(w for w in pe.child_list(d2)
             if win32gui.GetClassName(w) == 'Edit' and win32gui.IsWindowVisible(w))
    win32gui.SendMessage(e, win32con.WM_SETTEXT, 0, target)
    time.sleep(0.4)
    # 保存 = 给对话框发 IDOK 命令(不按回车, 不抢焦点)
    win32gui.SendMessage(d2, win32con.WM_COMMAND, win32con.IDOK, 0)
    t0 = time.time()
    while time.time() - t0 < 15:
        if os.path.exists(target) and os.path.getsize(target) > 500: break
        time.sleep(0.4)
        dismiss_dialogs(overwrite_yes=True)   # 覆盖确认等模态框兜底
    if not os.path.exists(target): return False
    # 内容核验: 渲染出的 PDF 头必须包含目标 dat 名(后台选择可能失手, 失手即重试一次)
    import pymupdf
    doc = pymupdf.open(target)
    head = doc[0].get_text()
    doc.close()
    if want in head: return True
    if os.path.exists(target): os.remove(target)
    pe.menu_cmd(h, 'File', 'Print')
    d = find_dlg(lambda x: win32gui.GetWindowText(x) in ('打印', 'Print'), 10)
    assert d, 'no print dialog (retry)'
    lb = next((w for w in pe.child_list(d) if win32gui.GetDlgCtrlID(w) == 1130), None)
    if lb:
        idx = lb_pick_by_text(lb, want)
        lb_select(lb, idx)
        time.sleep(0.3)
    set_bw(d)
    bg_ok(d)
    time.sleep(0.8)
    d2 = find_dlg(pe.is_saveas_dlg, 12)
    assert d2, 'no save-as (retry)'
    e = next(w for w in pe.child_list(d2)
             if win32gui.GetClassName(w) == 'Edit' and win32gui.IsWindowVisible(w))
    win32gui.SendMessage(e, win32con.WM_SETTEXT, 0, target)
    time.sleep(0.4)
    win32gui.SendMessage(d2, win32con.WM_COMMAND, win32con.IDOK, 0)
    t0 = time.time()
    while time.time() - t0 < 15:
        if os.path.exists(target) and os.path.getsize(target) > 500: break
        time.sleep(0.4)
        dismiss_dialogs(overwrite_yes=True)
    doc = pymupdf.open(target)
    head = doc[0].get_text()
    doc.close()
    return want in head


def _cjk_font():
    """返回 (fontname, fontfile):优先系统中文字体,避免内置 china-s 的字距拉宽。"""
    for f in (r'C:\Windows\Fonts\msyh.ttc',
              r'C:\Windows\Fonts\simsun.ttc',
              r'C:\Windows\Fonts\simhei.ttf'):
        if os.path.exists(f):
            return 'cjk', f
    return 'china-s', None


def thicken_trace(pdf, width_pt=1.2, min_segs=20):
    """加粗数据曲线:Probe 打印输出把所有描边都压成 hairline(0.5 用户单位),
    这里只对"含 >= min_segs 段 l 的路径"(=数据曲线)提高描边宽度,网格/边框不动。
    数据本身仍是 PSpice 原打印内容,只做线宽美化。"""
    import pymupdf, re
    doc = pymupdf.open(pdf)
    page = doc[0]
    page.clean_contents()
    xref = page.get_contents()[0]
    s = doc.xref_stream(xref).decode('latin-1')
    w = width_pt / 0.75          # 打印 CTM 为 0.75, 换算到用户单位
    pat = re.compile(r'((?:-?\d+(?:\.\d+)? -?\d+(?:\.\d+)? [ml]\s*)+)S')
    cnt = [0]

    def rep(m):
        body = m.group(1)
        if body.count(' l') < min_segs:
            return m.group(0)
        cnt[0] += 1
        return body + f'{w:.3f} w S 0.5 w'

    s2 = pat.sub(rep, s)
    if cnt[0]:
        doc.update_stream(xref, s2.encode('latin-1'))
        doc.save(pdf + '.thick', garbage=4, deflate=True)
        doc.close()
        os.replace(pdf + '.thick', pdf)
    else:
        doc.close()
    return cnt[0]


def annotate_pdf(pdf, caption=None, name=None):
    """在打印出的 PDF 上叠写标注(等比定位:图题左上、班级姓名右上)。
    Probe 内标注的 move-mode 放置依赖真实光标, 无法后台化; PDF 叠写是
    安静模式下的替代, 波形本体仍是软件原打印。"""
    import pymupdf
    doc = pymupdf.open(pdf)
    page = doc[0]
    W, H = page.rect.width, page.rect.height
    fontname, fontfile = _cjk_font()
    kw = dict(fontsize=11.5, fontname=fontname, color=(0, 0, 0))
    if fontfile:
        kw['fontfile'] = fontfile
    if caption:
        page.insert_text((W * 0.04, H * 0.035), caption, **kw)
    if name:
        kw['color'] = (0, 0, 0)
        page.insert_text((W * 0.78, H * 0.035), name, **kw)
    tmp = pdf + '.annot'
    if fontfile and (caption or name):
        # 嵌入的中文 TTC 默认整包 ~19MB;subset 后约 40KB
        try:
            doc.subset_fonts()
        except Exception:
            pass
        doc.save(tmp, garbage=4, deflate=True)
    else:
        doc.save(tmp)
    doc.close()
    os.replace(tmp, pdf)


def quiet_export(dat, out, traces, caption=None, name=None, two_frame=False):
    import win32api
    h = probe_frame()
    assert h, 'PSpice A/D 未启动'
    # 铁律:打印前关到只剩目标窗口(后台 WM_CLOSE+自动点否)
    quiet_close_all_children(h)
    quiet_open_dat(h, dat)
    if two_frame: quiet_two_frame(h, traces)
    else:
        for t in traces: quiet_add_trace(h, t)
    time.sleep(0.6)
    want = win32gui.GetWindowText(h).split('[')[-1].rstrip(']')
    for cycle in range(3):
        ok = quiet_print(h, out, want)
        if ok: break
    if not ok or not os.path.exists(out): return None
    # 标注: 安静模式用 PDF 叠写(move-mode 放置依赖真实光标, 无法后台化)
    thicken_trace(out, 1.2)
    annotate_pdf(out, caption, name)
    if not pdf_has(out, *( [k for k in (caption, name) if k] )):
        return None
    return out


def _cli():
    """命令行入口(安静模式), 供 skill/脚本直接调用:

      python orcad_quiet.py --dat tran.dat --out 图.pdf \
          --traces V(Vs) V(Vi) V(Vo) --caption "..." --name "信255 王保哲" [--two-frame]

    PSpice A/D(Probe) 需已打开目标 dat(可用 quiet_open_dat 或直接 pspice.exe dat)。
    """
    import argparse, sys
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser(description='quiet Probe export to PDF')
    ap.add_argument('--dat', required=True, help='tran.dat 全路径')
    ap.add_argument('--out', required=True, help='输出 PDF 全路径')
    ap.add_argument('--traces', nargs='+', default=['V(Vo)'])
    ap.add_argument('--caption', default=None)
    ap.add_argument('--name', default=None)
    ap.add_argument('--two-frame', action='store_true')
    a = ap.parse_args()
    res = quiet_export(a.dat, a.out, a.traces, caption=a.caption,
                       name=a.name, two_frame=a.two_frame)
    print(res if res else 'FAILED')
    return 0 if res else 1


if __name__ == '__main__':
    raise SystemExit(_cli())
