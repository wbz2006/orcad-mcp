"""exp4_dump_layout.py — 读取 PAGE2~5 全部布局: 元件/位号/位置/引脚热点/导线端点, 存 JSON"""
import sys, os, time, json
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
os.chdir(r"D:\Main_FIles\free-deng\orcad-mcp")
import bridge as br
import win32gui, win32con, win32api
import print_export as pe

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
print('agent ok')

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

result = {}
for pg in ('PAGE2', 'PAGE3', 'PAGE4', 'PAGE5'):
    s.eval(f'SelectPMItem {{{pg}}}', timeout=30)
    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0); time.sleep(0.06)
    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(2.2)
    tcl = HEADER + r'''
set pg [GetActivePage]
set out {{}}
# 元件
set it [$pg NewPartInstsIter $_st]
set i [$it NextPartInst $_st]
while { $i != $_null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $_null } {
        set rn "?"
        catch {{ set c [DboTclHelper_sMakeCString]; $pl GetReference $c; set rn [DboTclHelper_sGetConstCharPtr $c] }}
        set vl "?"
        catch {{ set c2 [DboTclHelper_sMakeCString]; $pl GetEffectivePropStringValue [DboTclHelper_sMakeCString "VALUE"] $c2; set vl [DboTclHelper_sGetConstCharPtr $c2] }}
        set lc [$pl GetLocation $_st]
        set lx [DboTclHelper_sGetCPointX $lc]
        set ly [DboTclHelper_sGetCPointY $lc]
        set pins {{}}
        set pit [$pl NewPinsIter $_st]
        set pin [$pit NextPin $_st]
        while { $pin != $_null } {
            set pn "?"
            catch {{ set c3 [DboTclHelper_sMakeCString]; $pin GetPinName $c3; set pn [DboTclHelper_sGetConstCharPtr $c3] }}
            set sp [$pin GetOffsetHotSpot $_st]
            lappend pins "$pn=[DboTclHelper_sGetCPointX $sp],[DboTclHelper_sGetCPointY $sp]"
            set pin [$pit NextPin $_st]
        }
        delete_DboPartInstPinsIter $pit
        lappend out "PART|$rn|$vl|$lx,$ly|[join $pins ,]"
    }
    set i [$it NextPartInst $_st]
}
delete_DboPagePartInstsIter $it
# 导线
set wit [$pg NewWiresIter $_st]
set w [$wit NextWire $_st]
while { $w != $_null } {
    set sp [$w GetStartPoint $_st]
    set ep [$w GetEndPoint $_st]
    set id [$w GetId $_st]
    lappend out "WIRE|$id|[DboTclHelper_sGetCPointX $sp],[DboTclHelper_sGetCPointY $sp]|[DboTclHelper_sGetCPointX $ep],[DboTclHelper_sGetCPointY $ep]"
    set w [$wit NextWire $_st]
}
delete_DboPageWiresIter $wit
join $out " || "
'''
    r = s.eval(tcl, timeout=60)
    result[pg] = r
    print(pg, 'dumped,', len(r), 'chars')
    # 切回工程管理器(避免标签残留状态)

json.dump(result, open(r'D:\Main_FIles\free-deng\orcad-mcp\exp4_layouts.json', 'w'), ensure_ascii=False, indent=1)
print('saved exp4_layouts.json')
