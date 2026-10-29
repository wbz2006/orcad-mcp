"""exp4_diag.py — 逐页打开 EXP4, 截图 + 页面信息, 诊断黑色框;尝试 F5 前后对比"""
import sys, os, time, subprocess
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
os.chdir(r"D:\Main_FIles\free-deng\orcad-mcp")
os.environ["ORCAD_MCP_PORT"] = "5178"
import bridge as br
import print_export as pe
from PIL import ImageGrab
import win32gui, win32con, win32api

OUT = r"D:\Main_FIles\free-deng\orcad-mcp\exp4shots"
os.makedirs(OUT, exist_ok=True)
CAP = r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\Capture.exe"
OPJ = r"D:\Users\Download\try\EXP4.opj"

env = dict(os.environ)
subprocess.Popen([CAP, OPJ], env=env)
time.sleep(4)

frame = None
t0 = time.time()
while time.time() - t0 < 60 and not frame:
    def cb(h, _):
        global frame
        t = win32gui.GetWindowText(h)
        if win32gui.IsWindowVisible(h) and 'OrCAD Capture CIS - Lite' in t: frame = frame or h
        return True
    win32gui.EnumWindows(cb, None)
    time.sleep(1)
assert frame, 'no frame'
print('frame:', frame)

# 启动桥, 等 agent
b = br.Bridge(5178)
b.ensure()
s = None
for _ in range(30):
    try:
        s = b.BRIDGE.session() if hasattr(b, 'BRIDGE') else None
        if s: break
    except Exception:
        pass
    # bridge(5178) 自身类无单例时用原始接口: 直接扫 sessions
    time.sleep(1)
    try:
        s = br.Bridge(5178).session()
    except Exception:
        s = None
# 上面模式不对,改用: Bridge 实例里 sessions 由 accept 线程填充
# 简化: 轮询 ensure+session
s = None
for _ in range(40):
    try:
        s = b.session(); break
    except Exception:
        time.sleep(1.5)
assert s, 'no agent'
print('agent connected')

# 恢复对话框清理(消息点击)
for _ in range(6):
    ds = []
    def cb2(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == '#32770': ds.append(h)
        return True
    win32gui.EnumWindows(cb2, None)
    if not ds: break
    for d in ds:
        btns = [(win32gui.GetDlgCtrlID(w), pe.get_text(w), w) for w in pe.child_list(d) if win32gui.GetClassName(w) == 'Button']
        tgt = next((w for i, t, w in btns if t.startswith('是')), None) or next((w for i, t, w in btns if i == 1), None)
        if tgt: win32gui.SendMessage(tgt, win32con.BM_CLICK, 0, 0)
        time.sleep(2)
t0 = time.time()
while time.time() - t0 < 60 and 'EXP4' not in win32gui.GetWindowText(frame):
    time.sleep(1)
print('title:', win32gui.GetWindowText(frame)[:70])

cap = []
def cb3(h, _):
    t = win32gui.GetWindowText(h)
    if win32gui.IsWindowVisible(h) and 'OrCAD Capture' in t: cap.append(h)
    return True
win32gui.EnumWindows(cb3, None)
h = cap[0]
tree = None
def scan(w, _):
    global tree
    if win32gui.GetClassName(w) == 'SysTreeView32': tree = w
    return True
win32gui.EnumChildWindows(h, scan, None)

def dark_ratio(img, box):
    im = img.crop(box).convert('L')
    px = list(im.getdata())
    dark = sum(1 for v in px if v < 60)
    return dark / max(1, len(px))

for pg in ('PAGE1', 'PAGE2', 'PAGE3', 'PAGE4', 'PAGE5'):
    s.eval(f'SelectPMItem {{{pg}}}', timeout=30)
    win32api.SetFocus(tree)
    win32api.keybd_event(0x0D, 0, 0, 0); time.sleep(0.05)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(2.5)
    win32api.SetForegroundWindow(h); time.sleep(0.5)
    img = ImageGrab.grab()
    img.save(os.path.join(OUT, f'{pg}.png'))
    # 画布暗像素比例(去掉左右树/面板, 取中间区域)
    W, H = img.size
    dr = dark_ratio(img, (int(W*0.18), int(H*0.12), int(W*0.95), int(H*0.9)))
    # 页面信息
    try:
        info = s.eval('set p [GetActivePage]; list [$p GetSizeName] [expr {[$p GetPageWidth]}] [expr {[$p GetPageHeight]}]', timeout=30)
    except Exception as e:
        info = f'ERR {e}'
    print(pg, 'dark=%.2f' % dr, 'info:', info)
print('DIAG DONE')
