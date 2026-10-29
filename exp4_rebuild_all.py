"""exp4_rebuild_all.py — PAGE3/4/5 批量重构: 单地线 + V1 移右上 + 删旧线路
PAGE4 同 PAGE2; PAGE3/5 同但 V3 引脚 (270,450)/(270,490), 删其旧桩线。
几何匹配删除(不硬编码 ID), 每页完成即存盘。"""
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
print('ready')

# 每页: 需删除的导线端点集(几何匹配)
OLD_WIRES = {
    'PAGE4': [((410,180),(600,180)), ((600,180),(600,270)), ((410,220),(410,260)), ((270,500),(270,560))],
    'PAGE3': [((410,180),(600,180)), ((600,180),(600,270)), ((410,220),(410,260)), ((270,450),(270,460)), ((270,500),(270,560))],
    'PAGE5': [((410,180),(600,180)), ((600,180),(600,270)), ((410,220),(410,260)), ((270,450),(270,460)), ((270,500),(270,560))],
}
# 每页: 需删除的地符号位置 (保留 (620,490))
DEL_GNDS = {'PAGE4': [(410,260),(270,560)], 'PAGE3': [(410,260),(270,560)], 'PAGE5': [(410,260),(270,560)]}
# 每页: 新增导线 (doc 单位)
NEW_WIRES = {
    'PAGE4': [(700,140,700,120), (700,120,600,120), (600,120,600,270), (270,500,270,470), (270,470,620,470)],
    'PAGE3': [(700,140,700,120), (700,120,600,120), (600,120,600,270), (270,490,270,470), (270,470,620,470)],
    'PAGE5': [(700,140,700,120), (700,120,600,120), (600,120,600,270), (270,490,270,470), (270,470,620,470)],
}

def dump_state(pg_var='pg'):
    tcl = HEADER + r'''
set pg [GetActivePage]
set out {}
set git [$pg NewGlobalsIter $_st]
set g [$git NextGlobal $_st]
while { $g != $_null } {
    set lc [$g GetLocation $_st]
    set id "?"
    catch { set id [$g GetId $_st] }
    lappend out "Gid=$id ([DboTclHelper_sGetCPointX $lc],[DboTclHelper_sGetCPointY $lc])"
    set g [$git NextGlobal $_st]
}
catch { delete_DboPageGlobalsIter $git }
set wit [$pg NewWiresIter $_st]
set w [$wit NextWire $_st]
while { $w != $_null } {
    set sp [$w GetStartPoint $_st]
    set ep [$w GetEndPoint $_st]
    set id [$w GetId $_st]
    lappend out "W$id ([DboTclHelper_sGetCPointX $sp],[DboTclHelper_sGetCPointY $sp])-([DboTclHelper_sGetCPointX $ep],[DboTclHelper_sGetCPointY $ep])"
    set w [$wit NextWire $_st]
}
catch { delete_DboPageWiresIter $wit }
join $out " | "
'''
    return s.eval(tcl, timeout=60)

def do_page(pg, old_wires, del_gnds, new_wires):
    s.eval(f'SelectPMItem {{{pg}}}', timeout=30)
    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0); time.sleep(0.06)
    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(2.2)
    state = dump_state()
    print(f'--- {pg} before:', state[:200], '...')

    # 1) 删旧导线 (几何匹配)
    ndel = 0
    for (p1, p2) in old_wires:
        tcl = HEADER + r'''
set pg [GetActivePage]
set wit [$pg NewWiresIter $_st]
set w [$wit NextWire $_st]
set found 0
while { $w != $_null && $found == 0 } {
    set sp [$w GetStartPoint $_st]
    set ep [$w GetEndPoint $_st]
    set sx [DboTclHelper_sGetCPointX $sp]; set sy [DboTclHelper_sGetCPointY $sp]
    set ex [DboTclHelper_sGetCPointX $ep]; set ey [DboTclHelper_sGetCPointY $ep]
    if { ($sx == P1X && $sy == P1Y && $ex == P2X && $ey == P2Y) || ($sx == P2X && $sy == P2Y && $ex == P1X && $ey == P1Y) } {
        set found [expr { [$w GetId $_st] }]
    }
    set w [$wit NextWire $_st]
}
catch { delete_DboPageWiresIter $wit }
if { $found == 0 } { return "nomatch" } else { return $found }
'''
        tcl = tcl.replace('P1X', str(p1[0])).replace('P1Y', str(p1[1])).replace('P2X', str(p2[0])).replace('P2Y', str(p2[1]))
        r = s.eval(tcl, timeout=60)
        if r == 'nomatch':
            print(f'  wire {p1}-{p2}: not found (skip)')
            continue
        try:
            s.eval(f'SelectObjectById {r}', timeout=30)
            s.eval('Menu "Edit::Delete"', timeout=30)
            ndel += 1
            time.sleep(0.5)
        except Exception as e:
            print(f'  wire {p1}-{p2} del ERR:', e)
    print(f'  wires deleted: {ndel}')

    # 2) 删多余地符号 (按位置匹配)
    for (gx, gy) in del_gnds:
        tcl = HEADER + r'''
set pg [GetActivePage]
set git [$pg NewGlobalsIter $_st]
set g [$git NextGlobal $_st]
set found 0
while { $g != $_null && $found == 0 } {
    set lc [$g GetLocation $_st]
    set lx [DboTclHelper_sGetCPointX $lc]; set ly [DboTclHelper_sGetCPointY $lc]
    if { $lx == {gx} && $ly == {gy} } { set found [expr { [$g GetId $_st] }] }
    set g [$git NextGlobal $_st]
}
catch { delete_DboPageGlobalsIter $git }
if { $found == 0 } { return "nomatch" } else { return $found }
'''
        tcl = tcl.replace('P1X', str(p1[0])).replace('P1Y', str(p1[1])).replace('P2X', str(p2[0])).replace('P2Y', str(p2[1]))
        r = s.eval(tcl, timeout=60)
        if r == 'nomatch':
            print(f'  gnd ({gx},{gy}): not found (skip)')
            continue
        try:
            s.eval(f'SelectObjectById {r}', timeout=30)
            s.eval('Menu "Edit::Delete"', timeout=30)
            print(f'  gnd ({gx},{gy}) deleted')
            time.sleep(0.5)
        except Exception as e:
            print(f'  gnd ({gx},{gy}) del ERR:', e)

    # 3) 移 V1 (400,180) -> (690,140)
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
    set i [$it NextPartInst $_st]
}
catch { delete_DboPagePartInstsIter $it }
set moved
'''
    r = s.eval(tcl_move, timeout=60)
    print('  V1 moved:', r)

    # 4) PlaceWire 新导线
    for (x1, y1, x2, y2) in new_wires:
        try:
            s.eval(f'PlaceWire {x1/100:.2f} {y1/100:.2f} {x2/100:.2f} {y2/100:.2f}', timeout=60)
            time.sleep(0.4)
        except Exception as e:
            print(f'  PlaceWire {x1},{y1}-{x2},{y2} ERR:', e)
    print('  wires placed:', len(new_wires))

    # 5) 存盘
    s.eval('Menu "File::Save"', timeout=45)
    time.sleep(1.5)
    state = dump_state()
    print(f'--- {pg} after:', state[:260], '...')

for pg in ('PAGE4', 'PAGE3', 'PAGE5'):
    do_page(pg, OLD_WIRES[pg], DEL_GNDS[pg], NEW_WIRES[pg])
print('ALL DONE')
