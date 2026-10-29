# -*- coding: utf-8 -*-
"""Agentless Capture automation: delete PAGE2-5 from EXP4.DSN via the
Project Manager tree using pure Win32 (no TCL agent -> no crashes)."""
import sys, os, time, subprocess, re, ctypes
from ctypes import wintypes

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui, win32con, win32api, win32process

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

TV_FIRST = 0x1100
TVM_GETITEMW = TV_FIRST + 62
TVM_SELECTITEM = TV_FIRST + 11
TVM_EXPAND = TV_FIRST + 2
TVM_GETNEXTITEM = TV_FIRST + 10
TVGN_ROOT, TVGN_NEXT, TVGN_CHILD, TVGN_CARET = 0, 1, 4, 9
TVIF_TEXT = 0x0001
TVIF_CHILDREN = 0x0040
TVE_EXPAND = 0x0002
PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
PAGE_READWRITE = 0x04

class TVITEMW32(ctypes.Structure):
    """TVITEMW layout for a 32-BIT target process (Capture.exe is 32-bit even
    on x64 Windows): every pointer/HANDLE field is 4 bytes. Total 40 bytes."""
    _fields_ = [
        ("mask", ctypes.c_uint32),          # UINT
        ("hItem", ctypes.c_uint32),         # HTREEITEM (4 bytes in 32-bit proc)
        ("state", ctypes.c_uint32),         # UINT
        ("stateMask", ctypes.c_uint32),     # UINT
        ("pszText", ctypes.c_uint32),       # LPWSTR (4 bytes!)
        ("cchTextMax", ctypes.c_int32),     # int
        ("iImage", ctypes.c_int32),         # int
        ("iSelectedImage", ctypes.c_int32), # int
        ("cChildren", ctypes.c_int32),      # int
        ("lParam", ctypes.c_uint32),        # LPARAM (4 bytes)
    ]

class RemoteTree:
    def __init__(self, htree):
        self.htree = htree
        tid, pid = win32process.GetWindowThreadProcessId(htree)
        self.pid = pid
        self.hproc = kernel32.OpenProcess(PROCESS_VM_OPERATION | PROCESS_VM_READ | PROCESS_VM_WRITE, False, pid)
        assert self.hproc, "OpenProcess failed"
        self.base = kernel32.VirtualAllocEx(self.hproc, None, 8192, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
        assert self.base, "VirtualAllocEx failed"
        self.item = TVITEMW32()
        self.item_bytes = ctypes.sizeof(TVITEMW32)
        assert self.item_bytes == 40, f"bad TVITEMW32 size {self.item_bytes}"
        assert self.base < 0x100000000, "remote base does not fit 32 bits"
        self.text_off = 256  # keep some slack after the struct

    def _write(self, offset, data):
        buf = ctypes.create_string_buffer(bytes(data), len(data))
        ok = kernel32.WriteProcessMemory(self.hproc, self.base + offset, buf, len(data), None)
        assert ok, "WriteProcessMemory failed"

    def _read(self, offset, size):
        buf = ctypes.create_string_buffer(size)
        ok = kernel32.ReadProcessMemory(self.hproc, self.base + offset, buf, size, None)
        assert ok, "ReadProcessMemory failed"
        return bytes(buf)

    def _pack_item(self, item):
        return bytes(item)  # ctypes struct -> raw (packed naturally, matches x64 ABI)

    def get_text(self, hitem):
        self.item.mask = TVIF_TEXT | TVIF_CHILDREN
        self.item.hItem = hitem
        self.item.pszText = self.base + self.text_off
        self.item.cchTextMax = 1024
        self._write(0, self._pack_item(self.item))
        # argtypes are critical: the 64-bit remote buffer address must not be
        # truncated to 32 bits by default ctypes conversion
        res = ctypes.c_size_t(0)
        user32.SendMessageTimeoutW(self.htree, TVM_GETITEMW, 0, ctypes.c_void_p(self.base),
                                   0x0002 | 0x0008, 4000, ctypes.byref(res))
        raw = self._read(self.text_off, 1024)
        return raw.decode("utf-16-le", errors="replace").split("\x00")[0]

    def next_item(self, hitem, flag):
        res = ctypes.c_void_p(user32.SendMessageW(self.htree, TVM_GETNEXTITEM, flag, hitem))
        return res.value or None

    def expand(self, hitem):
        user32.SendMessageW(self.htree, TVM_EXPAND, TVE_EXPAND, hitem)

    def select(self, hitem):
        user32.SendMessageW(self.htree, TVM_SELECTITEM, TVGN_CARET, hitem)

    def walk(self):
        """Return list of (hitem, text, depth)."""
        out = []
        def rec(h, depth):
            out.append((h, self.get_text(h), depth))
            child = self.next_item(h, TVGN_CHILD)
            while child:
                rec(child, depth + 1)
                child = self.next_item(child, TVGN_NEXT)
        root = self.next_item(None, TVGN_ROOT)
        while root:
            rec(root, 0)
            root = self.next_item(root, TVGN_NEXT)
        return out

    def close(self):
        kernel32.VirtualFreeEx(self.hproc, self.base, 0, 0x8000)
        kernel32.CloseHandle(self.hproc)

def get_text_win(h):
    b = ctypes.create_unicode_buffer(300)
    user32.SendMessageTimeoutW(h, win32con.WM_GETTEXT, 300, ctypes.cast(b, ctypes.c_void_p),
                               0x0002 | 0x0008, 3000, ctypes.byref(ctypes.c_size_t(0)))
    return b.value

def dialogs():
    out = []
    def cb(h, _):
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "#32770" and t:
            out.append((h, t))
        return True
    win32gui.EnumWindows(cb, None)
    return out

def find_btn(dlg, txt):
    out = []
    win32gui.EnumChildWindows(dlg, lambda c, _: out.append((c, get_text_win(c))) if win32gui.GetClassName(c) == "Button" else None, None)
    for cc, tt in out:
        if txt in tt: return cc
    return None

def frame():
    out = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in win32gui.GetWindowText(h):
            out.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return out[0] if out else None

def pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Capture.exe", "/FO", "CSV"],
                         capture_output=True).stdout.decode("gbk", errors="replace")
    return [p for p in re.findall(r'"Capture.exe","(\d+)"', out) if p not in ("40484", "51440", "1524")]

def drain(rnds=12):
    for _ in range(rnds):
        ds = dialogs()
        if not ds: return
        for h, t in ds:
            print("  DLG:", t, flush=True)
            if t == "Select Project Type":
                r = find_btn(h, "Analog or Mixed")
                if r: win32gui.PostMessage(r, 0x00F5, 0, 0); time.sleep(1)
                ok = find_btn(h, "OK")
                if ok: win32gui.PostMessage(ok, 0x00F5, 0, 0)
            else:
                ids = []
                win32gui.EnumChildWindows(h, lambda c, _: ids.append(win32gui.GetDlgCtrlID(c)) if win32gui.GetClassName(c) == "Button" and win32gui.IsWindowVisible(c) else None, None)
                # prefer Yes(6)/OK(1)/Cancel(2)
                if 6 in ids: win32gui.PostMessage(h, win32con.WM_COMMAND, 6, 0)
                elif 1 in ids: win32gui.PostMessage(h, win32con.WM_COMMAND, 1, 0)
                elif 2 in ids: win32gui.PostMessage(h, win32con.WM_COMMAND, 2, 0)
            time.sleep(2)
        time.sleep(1.2)

def main():
    env = dict(os.environ)
    env.setdefault("ORCAD_MCP_PORT", "5178")
    # launch Capture with the DSN
    if not pids():
        subprocess.Popen([r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\Capture.exe",
                          r"D:\Users\Download\try\EXP4.DSN"], env=env)
        print("launched with DSN", flush=True)
        time.sleep(8)
        drain(20)
        time.sleep(3)
    f = frame()
    assert f, "no Capture frame"
    print("frame:", win32gui.GetWindowText(f), flush=True)

    # find the tree in the PM MDI child (wait for project to fully open)
    rt = None
    for i in range(60):
        trees = []
        def tb(h, _):
            if win32gui.GetClassName(h) == "SysTreeView32":
                trees.append(h)
            return True
        ff = frame()
        if ff:
            trees = []
            win32gui.EnumChildWindows(ff, tb, None)
        if trees:
            rt = RemoteTree(trees[0])
            print(f"tree found at t={i*3}s: {trees[0]}", flush=True)
            break
        drain(3)
        time.sleep(3)
    assert rt, "no tree found"
    items = rt.walk()
    for h, t, d in items:
        print("  " * (d + 1) + f"{t}  (h={h})", flush=True)
    # expand everything with children first
    for h, t, d in items:
        rt.expand(h)
    time.sleep(1)
    items = rt.walk()
    print("--- after expand ---", flush=True)
    for h, t, d in items:
        print("  " * (d + 1) + f"{t}  (h={h})", flush=True)

    # ensure pages under SCHEMATIC1 are actually visible: select the node and
    # send RIGHT (expand one level) until PAGE1..PAGE5 appear in the walk
    def pages_visible():
        texts = [t for _, t, _ in rt.walk()]
        return "PAGE1" in texts and "PAGE5" in texts

    for attempt in range(6):
        if pages_visible():
            break
        print(f"pages not visible (attempt {attempt}); forcing expand", flush=True)
        sch = None
        for h, t, d in rt.walk():
            if t.strip().upper() == "SCHEMATIC1":
                sch = h; break
        if not sch:
            print("SCHEMATIC1 node not found!", flush=True)
            break
        rt.select(sch)
        try: win32gui.SetForegroundWindow(f)
        except Exception: pass
        time.sleep(0.5)
        win32api.keybd_event(win32con.VK_RIGHT, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_RIGHT, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(1.5)
    print("--- pages check ---", flush=True)
    for h, t, d in rt.walk():
        print("  " * (d + 1) + f"{t}  (h={h})", flush=True)
    assert pages_visible(), "PAGE1..PAGE5 not visible under SCHEMATIC1"

    # delete PAGE2..5
    for pg in ["PAGE2", "PAGE3", "PAGE4", "PAGE5"]:
        target = None
        for h, t, d in rt.walk():
            if t == pg:
                target = h; break
        if not target:
            print(f"{pg}: absent (ok)", flush=True); continue
        rt.select(target)
        time.sleep(0.8)
        # bring frame forward and send DELETE to the tree
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
        try: win32gui.SetForegroundWindow(f)
        except Exception: pass
        time.sleep(0.6)
        win32api.keybd_event(win32con.VK_DELETE, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(win32con.VK_DELETE, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(1.5)
        # handle confirm dialog
        ds = dialogs()
        for h, t in ds:
            print(f"  {pg} confirm DLG:", t, flush=True)
            ids = []
            win32gui.EnumChildWindows(h, lambda c, _: ids.append(win32gui.GetDlgCtrlID(c)) if win32gui.GetClassName(c) == "Button" and win32gui.IsWindowVisible(c) else None, None)
            if 6 in ids: win32gui.PostMessage(h, win32con.WM_COMMAND, 6, 0)
            elif 1 in ids: win32gui.PostMessage(h, win32con.WM_COMMAND, 1, 0)
            elif 2 in ids: win32gui.PostMessage(h, win32con.WM_COMMAND, 2, 0)
            time.sleep(1.5)
        drain(4)
        left = [t for _, t, _ in rt.walk()]
        print(f"{pg} deleted, still present: {'YES' if pg in left else 'no'}", flush=True)

    # save via Ctrl+S
    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
    try: win32gui.SetForegroundWindow(f)
    except Exception: pass
    time.sleep(0.6)
    m0 = os.path.getmtime(r"D:\Users\Download\try\EXP4.DSN")
    win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    win32api.keybd_event(ord('S'), 0, 0, 0)
    time.sleep(0.06)
    win32api.keybd_event(ord('S'), 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
    saved = False
    for _ in range(12):
        time.sleep(1)
        drain(3)
        if os.path.getmtime(r"D:\Users\Download\try\EXP4.DSN") != m0:
            saved = True; break
    print("SAVED" if saved else "save FAILED", flush=True)
    drain(5)
    rt.close()

if __name__ == "__main__":
    main()
