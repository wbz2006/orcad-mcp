"""exp4_wires.py — 用 raw bridge + MCP 同款头, 枚举 EXP4 PAGE1 导线与 Q1 引脚"""
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
s.eval('SelectPMItem {PAGE1}', timeout=30)
win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0); time.sleep(0.06)
win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(2.2)
print('PAGE1 opened')

tcl = HEADER + '''
set pg [GetActivePage]
set out {}
set wit [$pg NewWiresIter $_st]
set w [$wit NextWire $_st]
while { $w != $_null } {
    set sp [$w GetStartPoint $_st]
    set ep [$w GetEndPoint $_st]
    set id [$w GetId $_st]
    lappend out "W$id ([DboTclHelper_sGetCPointX $sp],[DboTclHelper_sGetCPointY $sp])-([DboTclHelper_sGetCPointX $ep],[DboTclHelper_sGetCPointY $ep])"
    set w [$wit NextWire $_st]
}
delete_DboPageWiresIter $wit
set it [$pg NewPartInstsIter $_st]
set i [$it NextPartInst $_st]
while { $i != $_null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $_null } {
        set rn "?"
        catch { set c [DboTclHelper_sMakeCString]; $pl GetReference $c; set rn [DboTclHelper_sGetConstCharPtr $c] }
        if { $rn == "Q1" } {
            set pit [$pl NewPinsIter $_st]
            set pin [$pit NextPin $_st]
            while { $pin != $_null } {
                set pn "?"
                catch { set c2 [DboTclHelper_sMakeCString]; $pin GetPinName $c2; set pn [DboTclHelper_sGetConstCharPtr $c2] }
                set sp [$pin GetOffsetHotSpot $_st]
                lappend out "Q1.$pn=([DboTclHelper_sGetCPointX $sp],[DboTclHelper_sGetCPointY $sp])"
                set pin [$pit NextPin $_st]
            }
            delete_DboPartInstPinsIter $pit
        }
    }
    set i [$it NextPartInst $_st]
}
delete_DboPagePartInstsIter $it
join $out " | "
'''
r = s.eval(tcl, timeout=60)
print(r)
