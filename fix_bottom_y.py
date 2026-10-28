"""fix_bottom_y.py — 一次性修好下坐标系 Y 量程: 全程回读验证"""
import time, win32gui, win32con, win32api, ctypes
import print_export as pe

u32 = ctypes.windll.user32

def wait_dead(d, timeout=5):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if not win32gui.IsWindow(d): return True
        time.sleep(0.3)
    return not win32gui.IsWindow(d)

def main():
    h = pe.probe_frame()
    pe.set_fore(h)
    assert pe.menu_cmd(h, 'Plot', 'Axis Settings')
    d = pe.find_dlg(lambda x: 'Axis Settings' in win32gui.GetWindowText(x), 6)
    assert d, 'no dialog'
    print('dlg:', d)
    pe.set_fore(d); time.sleep(0.6)

    tab = next(w for w in pe.child_list(d) if win32gui.GetClassName(w) == 'SysTabControl32')
    # 切到 Y 页: 直接消息点击 Y 标签 + RIGHT 兜底, TCM_GETCURFOCUS 验证
    ok = False
    for i in range(4):
        lp = (161 << 16) | 355
        win32gui.SendMessage(tab, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lp)
        time.sleep(0.08)
        win32gui.SendMessage(tab, win32con.WM_LBUTTONUP, 0, lp)
        time.sleep(0.5)
        cur = win32gui.SendMessage(tab, 0x132F, 0, 0)
        if cur != 1:
            win32api.keybd_event(win32con.VK_RIGHT, 0, 0, 0); time.sleep(0.06)
            win32api.keybd_event(win32con.VK_RIGHT, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.6)
            cur = win32gui.SendMessage(tab, 0x132F, 0, 0)
        print(f'try{i}: curfocus={cur}')
        if cur == 1: ok = True; break
    assert ok, 'cannot switch to Y page'
    time.sleep(1.0)  # 等 DDX 填充

    # 找 Y 页电压编辑框
    pairs = {}
    for w in pe.child_list(d):
        if win32gui.GetClassName(w) == 'Edit':
            cid = win32gui.GetDlgCtrlID(w); t = pe.get_text(w)
            if cid in (1029, 1030) and 'V' in t: pairs[cid] = w
    print('y edits:', [(c, pe.get_text(w)) for c, w in pairs.items()])
    assert 1029 in pairs and 1030 in pairs, 'Y edits not found'
    win32gui.SendMessage(pairs[1029], win32con.WM_SETTEXT, 0, '-20mV')
    win32gui.SendMessage(pairs[1030], win32con.WM_SETTEXT, 0, '20mV')
    time.sleep(0.3)
    got = (pe.get_text(pairs[1029]), pe.get_text(pairs[1030]))
    print('readback:', got)
    assert got == ('-20mV', '20mV'), 'edit set failed'

    # UD 单选: 点 + BM_GETCHECK 验证
    for i in range(3):
        pe.click(601, 415); time.sleep(0.5)
        st = {}
        for w in pe.child_list(d):
            if win32gui.GetClassName(w) == 'Button' and win32gui.GetDlgCtrlID(w) in (1004, 1005):
                r = win32gui.GetWindowRect(w)
                if 380 < r[1] < 470:
                    st.setdefault(win32gui.GetDlgCtrlID(w), []).append(
                        win32gui.SendMessage(w, 0x00F0, 0, 0))
        print(f'radio try{i}:', st)
        if 1005 in st and 1 in st[1005]: break
    else:
        raise AssertionError('UD radio not checked')

    pe.click(571, 701)  # OK
    assert wait_dead(d), 'dialog not closed'
    print('committed; verifying...')

    # 重开验证
    assert pe.menu_cmd(h, 'Plot', 'Axis Settings')
    d2 = pe.find_dlg(lambda x: 'Axis Settings' in win32gui.GetWindowText(x), 6)
    assert d2, 'reopen failed'
    time.sleep(0.8)
    tab2 = next(w for w in pe.child_list(d2) if win32gui.GetClassName(w) == 'SysTabControl32')
    for i in range(4):
        lp = (161 << 16) | 355
        win32gui.SendMessage(tab2, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lp)
        time.sleep(0.08)
        win32gui.SendMessage(tab2, win32con.WM_LBUTTONUP, 0, lp)
        time.sleep(0.5)
        cur = win32gui.SendMessage(tab2, 0x132F, 0, 0)
        if cur != 1:
            win32api.keybd_event(win32con.VK_RIGHT, 0, 0, 0); time.sleep(0.06)
            win32api.keybd_event(win32con.VK_RIGHT, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.6)
            cur = win32gui.SendMessage(tab2, 0x132F, 0, 0)
        if cur == 1: break
    time.sleep(1.0)
    vals = []
    for w in pe.child_list(d2):
        if win32gui.GetClassName(w) == 'Edit':
            cid = win32gui.GetDlgCtrlID(w); t = pe.get_text(w)
            if cid in (1029, 1030) and 'V' in t: vals.append((cid, t))
    print('verify reopen:', vals)
    c2 = next(w for w in pe.child_list(d2)
              if win32gui.GetClassName(w) == 'Button' and win32gui.GetDlgCtrlID(w) == 2)
    win32gui.SendMessage(c2, win32con.BM_CLICK, 0, 0)
    wait_dead(d2)
    ok = any(t == '-20mV' for _, t in vals) and any(t == '20mV' for _, t in vals)
    print('BOTTOM Y RANGE FIXED:', ok)
    return ok

if __name__ == '__main__':
    main()
