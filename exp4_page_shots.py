"""exp4_page_shots.py — 起桥 → agent 回连 → 逐页打开 EXP4 并截图(复现黑色框)"""
import sys, os, time, socket
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
os.chdir(r"D:\Main_FIles\free-deng\orcad-mcp")
import bridge
import print_export as pe
from PIL import ImageGrab
import win32gui, win32con, win32api

OUT = r"D:\Main_FIles\free-deng\orcad-mcp\exp4shots"
os.makedirs(OUT, exist_ok=True)

# 起桥(agent 每 4s 重连一次)
b = bridge.Bridge()
b.ensure()
print("bridge listening")
s = None
for i in range(20):
    try:
        s = b.session(); break
    except RuntimeError:
        time.sleep(1)
assert s, "no agent connected"
print("agent connected")
s.eval('SelectPMItem {PAGE1}', timeout=30)
r = s.eval('GetActivePage GetName', timeout=30)
print("active page:", r)

# 找 Capture 框架与工程树
cap = []
def cb(h, _):
    t = win32gui.GetWindowText(h)
    if win32gui.IsWindowVisible(h) and 'OrCAD Capture' in t: cap.append(h)
    return True
win32gui.EnumWindows(cb, None)
h = cap[0]
pe.set_fore(h); time.sleep(0.5)
tree = None
def scan(w, _):
    global tree
    if win32gui.GetClassName(w) == 'SysTreeView32': tree = w
    return True
win32gui.EnumChildWindows(h, scan, None)
print("tree:", tree)

pages = ['PAGE1', 'PAGE2', 'PAGE3', 'PAGE4', 'PAGE5']
for pg in pages:
    s.eval(f'SelectPMItem {{{pg}}}', timeout=30)
    # 树上回车打开
    win32api.SetFocus(tree)
    win32api.keybd_event(0x0D, 0, 0, 0); time.sleep(0.05)
    win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(2.5)
    win32api.SetForegroundWindow(h); time.sleep(0.4)
    ImageGrab.grab().save(os.path.join(OUT, f"{pg}.png"))
    print(pg, "shot saved")
print("ALL DONE")
