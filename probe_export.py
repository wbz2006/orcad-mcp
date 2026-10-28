"""probe_export.py — Probe 波形图软件导出一站式脚本(v1, 迭代1 沉淀)
用法:
  python probe_export.py <dat文件> <输出pdf> --traces V(Vs),V(Vi),V(Vo) [--two-frame]
                         --caption "IC=2mA 时的Vi、Vs、Vo 波形" --name "信255 王保哲"
流程:File>Open dat → Add Trace(s) → (可选双坐标系) → move-mode 标注 →
      File>Print → "Plots to Print" LB_SETSEL 选本窗口 → Save As。
前置:Probe(pspice.exe)已启动;Microsoft Print to PDF 为默认打印机。
"""
import sys, time, win32gui, win32con, os
import print_export as pe


def probe_open_dat(h, dat_path):
    for attempt in range(3):
        assert pe.menu_cmd(h, 'File', 'Open')
        d = pe.find_dlg(lambda x: win32gui.GetWindowText(x) in ('打开', 'Open'), 6)
        if d: break
        time.sleep(1)
    assert d, 'no open dialog'
    pe.set_fore(d)
    e = next(w for w in pe.child_list(d)
             if win32gui.GetClassName(w) == 'Edit' and win32gui.IsWindowVisible(w))
    win32gui.SendMessage(e, win32con.WM_SETTEXT, 0, dat_path)
    time.sleep(0.4)
    btn = next(w for w in pe.child_list(d)
               if win32gui.GetClassName(w) == 'Button' and win32gui.GetDlgCtrlID(w) == 1)
    win32gui.SendMessage(btn, win32con.BM_CLICK, 0, 0)
    name = os.path.basename(dat_path)
    t0 = time.time()
    while time.time() - t0 < 12:
        if name in win32gui.GetWindowText(h).lower(): break
        time.sleep(0.4)
    assert name in win32gui.GetWindowText(h).lower(), 'dat not opened'
    time.sleep(1.5)


def probe_label_move_mode(h, text, place_xy=(600, 300)):
    """Plot>Label>Text: OK 后状态栏进入 Move the text 模式,物理点击放置。
    只有这种方式放置的标签保证进入打印输出。
    place_xy 前会重新置顶+前台化 Capture 抢焦点问题(Start Page 已关仍可能发生)。"""
    win32gui.SetWindowPos(h, -1, 0, 0, 0, 0, 0x0001 | 0x0002)   # 重新置顶
    win32gui.PostMessage(h, win32con.WM_COMMAND, 0x802e, 0)
    d = pe.find_dlg(lambda x: 'Label Text' in win32gui.GetWindowText(x), 6)
    assert d, 'no label dialog'
    pe.set_fore(d)
    e = next(w for w in pe.child_list(d) if win32gui.GetClassName(w) == 'Edit')
    win32gui.SendMessage(e, win32con.WM_SETTEXT, 0, text)
    time.sleep(0.3)
    btn = next(w for w in pe.child_list(d)
               if win32gui.GetClassName(w) == 'Button' and win32gui.GetDlgCtrlID(w) == 1)
    win32gui.SendMessage(btn, win32con.BM_CLICK, 0, 0)
    time.sleep(1.2)
    win32gui.SetWindowPos(h, -1, 0, 0, 0, 0, 0x0001 | 0x0002)   # 放置前再保一次顶
    pe.set_fore(h)
    time.sleep(0.3)
    pe.click(*place_xy)
    time.sleep(0.8)


def probe_print_active(h, target, plots_lb_id=1130, ok_at=(824, 655)):
    """File>Print, 在 Plots to Print 里 LB_SETSEL 选本窗口(按标题文本匹配),
    OK, Save As 填路径。"""
    import win32print
    if os.path.exists(target): os.remove(target)
    win32print.SetDefaultPrinter('Microsoft Print to PDF')
    assert pe.menu_cmd(h, 'File', 'Print')
    d = pe.find_dlg(lambda x: win32gui.GetWindowText(x) in ('打印', 'Print'), 8)
    assert d, 'no print dialog'
    pe.set_fore(d); time.sleep(0.5)
    lb = next(w for w in pe.child_list(d) if win32gui.GetDlgCtrlID(w) == plots_lb_id)
    cnt = win32gui.SendMessage(lb, 0x018B, 0, 0)  # LB_GETCOUNT
    want = win32gui.GetWindowText(h).split('[')[-1].rstrip(']')
    pick = 0
    for i in range(cnt):
        ln = win32gui.SendMessage(lb, 0x018A, i, 0)  # LB_GETTEXTLEN
        buf = win32gui.PyMakeBuffer(ln * 2 + 8)
        win32gui.SendMessage(lb, 0x0189, i, buf)
        s = bytes(buf)[:ln * 2].decode('utf-16-le', 'ignore').split('\x00')[0]
        if want in s or (want in s.replace('(A) ', '').replace('(B) ', '')):
            pick = i
        if cnt == 1: pick = 0
    win32gui.SendMessage(lb, 0x0185, 1, pick)      # LB_SETSEL TRUE, pick
    time.sleep(0.2)
    win32gui.SendMessage(d, win32con.WM_COMMAND, (1 << 16) | plots_lb_id, lb)
    time.sleep(0.3)
    pe.click(*ok_at)                                # OK
    time.sleep(0.8)
    d2 = pe.find_dlg(pe.is_saveas_dlg, 12)
    assert d2, 'no save-as dialog'
    pe.set_fore(d2)
    assert pe.fill_first_edit(d2, target)
    pe.press(13)
    assert pe.wait_file(target), 'pdf not written'
    return target


def main():
    a = sys.argv[1:]
    dat = a[0]
    out = a[1]
    traces = []
    two = False; caption = None; name = None
    i = 2
    while i < len(a):
        if a[i] == '--traces': traces = a[i+1].split(','); i += 2
        elif a[i] == '--two-frame': two = True; i += 1
        elif a[i] == '--caption': caption = a[i+1]; i += 2
        elif a[i] == '--name': name = a[i+1]; i += 2
        else: i += 1
    h = pe.probe_frame()
    assert h, 'PSpice A/D 未启动'
    pe.set_fore(h)
    win32gui.SetWindowPos(h, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
    time.sleep(0.5)
    probe_open_dat(h, dat)
    if two:
        # 下坐标系: 先加前两条, 再 Add Plot to Window 放最后一条
        from probe_fig318 import add_trace
        for t in traces[:-1]: add_trace(h, t)
        assert pe.menu_cmd(h, 'Plot', 'Add Plot to Window')
        time.sleep(1.2)
        add_trace(h, traces[-1])
    else:
        from probe_fig318 import add_trace
        for t in traces: add_trace(h, t)
    time.sleep(0.8)
    if caption:
        probe_label_move_mode(h, caption, (600, 300))    # 0V 线中部
    if name:
        probe_label_move_mode(h, name, (1000, 300))      # 右侧
    ok = probe_print_active(h, out)
    print('EXPORTED:', ok, os.path.getsize(ok))

if __name__ == '__main__':
    main()
