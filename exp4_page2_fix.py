"""exp4_page2_fix.py — PAGE2 重构: 单地线 + V1 移到右上(对齐图4.15)"""
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

# 1) 原生删除 3 根旧线 (V1+ 老路径×2, V1- 老桩)
for wid in (135, 257, 266):
    try:
        s.eval(f'SelectObjectById {wid}', timeout=30)
        s.eval('Menu "Edit::Delete"', timeout=30)
        print(f'wire {wid} deleted')
        time.sleep(0.6)
    except Exception as e:
        print(f'wire {wid} ERR:', e)

# 2) 原生删除 V2 下的地符号 id=224 (保留 M2.S 的 id=228)
try:
    s.eval('SelectObjectById 224', timeout=30)
    s.eval('Menu "Edit::Delete"', timeout=30)
    print('gnd 224 deleted')
    time.sleep(0.6)
except Exception as e:
    print('gnd 224 ERR:', e)

# 3) SetLocation V1 -> (690,140) (按位置识别: 400,180 处的两脚元件)
tcl_move = HEADER + '''
set pg [GetActivePage]
set it [$pg NewPartInstsIter $_st]
set i [$it NextPartInst $_st]
set moved 0
while { $i != $_null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $_null } {
        set lc [$pl GetLocation $_st]
        set lx [DboTclHelper_sGetCPointX $lc]
        set ly [DboTclHelper_sGetCPointY $lc]
        if { $lx == 400 && $ly == 180 } {
            catch { $pl SetLocation [DboTclHelper_sMakeCPoint 690 140] }
            set moved 1
        }
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
set moved
'''
r = s.eval(tcl_move, timeout=60)
print('V1 moved:', r)

# 4) PlaceWire 补 3 段新线 (V1+ -> 上 -> 左 -> R1 顶)
for w in ('7.00 1.40 7.00 1.20', '7.00 1.20 6.00 1.20', '6.00 1.20 6.00 2.70'):
    try:
        s.eval(f'PlaceWire {w}', timeout=60)
        print('wire placed:', w)
        time.sleep(0.5)
    except Exception as e:
        print('PlaceWire ERR:', w, e)

# 5) 保存
s.eval('Menu "File::Save"', timeout=45)
print('saved')
time.sleep(1.5)

# 6) 状态核验
tcl_chk = HEADER + '''
set pg [GetActivePage]
set out {}
set git [$pg NewGlobalsIter $_st]
set g [$git NextGlobal $_st]
while { $g != $_null } {
    set lc [$g GetLocation $_st]
    lappend out "G([DboTclHelper_sGetCPointX $lc],[DboTclHelper_sGetCPointY $lc])"
    set g [$git NextGlobal $_st]
}
catch { delete_DboPageGlobalsIter $git }
set wit [$pg NewWiresIter $_st]
set w [$wit NextWire $_st]
set nw 0
set wl {}
while { $w != $_null } {
    incr nw
    set sp [$w GetStartPoint $_st]
    set ep [$w GetEndPoint $_st]
    lappend wl "([DboTclHelper_sGetCPointX $sp],[DboTclHelper_sGetCPointY $sp])-([DboTclHelper_sGetCPointX $ep],[DboTclHelper_sGetCPointY $ep])"
    set w [$wit NextWire $_st]
}
catch { delete_DboPageWiresIter $wit }
lappend out "wires=$nw"
lappend out [join $wl " "]
join $out " || "
'''
r = s.eval(tcl_chk, timeout=60)
print('VERIFY:', r)
