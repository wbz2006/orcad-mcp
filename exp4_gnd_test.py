"""exp4_gnd_test.py — 枚举 PAGE2 的地符号(globals), 测试原生删除多余 2 个"""
import sys, os, time
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
os.chdir(r"D:\Main_FIles\free-deng\orcad-mcp")
import bridge as br
import print_export as pe
import win32gui, win32con, win32api

HEADER = '''
if { [catch { set _s $::DboSession_s_pDboSession }] } { return "no Dbo session" }
DboSession -this $_s
set _st [DboState]
set _null NULL
'''

b = br.Bridge(5178); b.ensure()
s = None
for _ in range(15):
    try:
        s = b.session(); break
    except Exception: time.sleep(1)
assert s, 'no agent'

cap = []
def cb(h, _):
    t = win32gui.GetWindowText(h)
    if win32gui.IsWindowVisible(h) and 'OrCAD Capture' in t: cap.append(h)
    return True
win32gui.EnumWindows(cb, None)
h = cap[0]
pe.set_fore(h); time.sleep(0.4)
tree = None
def scan(w, _):
    global tree
    if win32gui.GetClassName(w) == 'SysTreeView32': tree = w
    return True
win32gui.EnumChildWindows(h, scan, None)
s.eval('SelectPMItem {PAGE2}', timeout=30)
win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0); time.sleep(0.06)
win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(2.2)
print('PAGE2 active')

tcl = HEADER + '''
set pg [GetActivePage]
set out {}
set git [$pg NewGlobalsIter $_st]
set g [$git NextGlobal $_st]
while { $g != $_null } {
    set nm "?"
    catch { set c [DboTclHelper_sMakeCString]; $g GetName $c; set nm [DboTclHelper_sGetConstCharPtr $c] }
    set id "?"
    catch { set id [$g GetId $_st] }
    set lc "?"
    catch { set lc [$g GetLocation $_st] }
    set lx "?"; set ly "?"
    catch { set lx [DboTclHelper_sGetCPointX $lc]; set ly [DboTclHelper_sGetCPointY $lc] }
    lappend out "G id=$id name=$nm at=($lx,$ly)"
    set g [$git NextGlobal $_st]
}
delete_DboPageGlobalsIter $git
join $out " | "
'''
r = s.eval(tcl, timeout=60)
print('GLOBALS:', r)
