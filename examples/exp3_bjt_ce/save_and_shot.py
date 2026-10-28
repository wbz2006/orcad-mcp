# -*- coding: utf-8 -*-
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
dx.ensure_capture(); s = br.BRIDGE.session()
s.eval('SelectPMItem {SCHEMATIC1}', 60); time.sleep(1)
print("save:", s.eval('Menu "File::Save"', 60)); time.sleep(2)
import win32gui, win32con, win32api
frame = win32gui.FindWindow("OrCaptureFrame", None)
rect = win32gui.GetWindowRect(frame)
win32gui.ShowWindow(frame, win32con.SW_MAXIMIZE); win32gui.BringWindowToTop(frame)
HWND_TOPMOST=-1; SWP_NOMOVE=0x0002; SWP_NOSIZE=0x0001
win32gui.SetWindowPos(frame, HWND_TOPMOST, 0,0,0,0, SWP_NOMOVE|SWP_NOSIZE); time.sleep(0.4)
if win32gui.GetForegroundWindow() != frame:
    win32api.SetCursorPos((rect[0]+400, rect[1]+12))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0); time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0); time.sleep(0.6)
s.eval('SelectPMItem {PAGE1}', 60); time.sleep(0.4)
win32api.keybd_event(win32con.VK_RETURN,0,0,0); win32api.keybd_event(win32con.VK_RETURN,0,win32con.KEYEVENTF_KEYUP,0)
time.sleep(3)
print("page:", s.eval('GetActivePage', 30))
TCL = r'''
set pg [GetActivePage]
set st [DboState]
set out {}
foreach pt { {960 190} {960 230} {90 590} {330 590} {570 590} {630 590} {840 330} {550 190} } {
    set p [DboTclHelper_sMakeCPoint [lindex $pt 0] [lindex $pt 1]]
    lappend out "conn $pt = [$pg GetConnectionCount $p $st]"
}
return $out
'''
print(s.eval(TCL, 60))
from PIL import ImageGrab
ImageGrab.grab().save(os.path.join(BASE, "screen46.png"))
print("shot ok")
