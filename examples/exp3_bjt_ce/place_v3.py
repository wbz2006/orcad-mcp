"""v3 放置:R/C/Q (PlaceNew) + 复制 VDC (真电池) + 剪贴板粘贴 VSIN (Vs)."""
import sys, os, time, json
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE); sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(BASE)
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
import build_exp3
from build_exp3 import parse_insts, find_click_point, click, TCL_LIST_INSTS, SET_ROT_HELPER

dx.ensure_capture()
s = br.BRIDGE.session()
CLICK = find_click_point()
build_exp3.CLICK_FIXED = CLICK
print("click:", CLICK)

PARTS = [
    # name  lib                                        pkg   rot   tx    ty
    ("Rs",  "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "R", 0, 2.2, 6.5),
    ("C1",  "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "C", 0, 3.4, 6.5),
    ("Rb1", "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "R", 1, 4.4, 4.8),
    ("Rc",  "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "R", 1, 6.5, 4.8),
    ("Rb2", "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "R", 1, 4.4, 7.0),
    ("Q1",  "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/eval.olb",  "Q2N3904", 0, 5.4, 6.1),
    ("Re",  "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "R", 1, 6.7, 7.0),
    ("Ce",  "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "C", 1, 7.7, 7.0),
    ("C2",  "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "C", 0, 7.3, 4.5),
    ("RL",  "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "R", 1, 9.1, 5.8),
]

for name, lib, pkg, rot, tx, ty in PARTS:
    s.eval(f'PlaceNew "{lib}" {pkg} 0', 60)
    time.sleep(0.3)
    click()
    s.eval('EndPlace; UnSelectAll', 60)
    time.sleep(0.35)
    insts = parse_insts(s.eval(dx.SETUP_TCL + SET_ROT_HELPER + TCL_LIST_INSTS, 120))
    new = [i for i in insts if len(i["pins"]) == (3 if name == "Q1" else 2)
           and abs(i["loc"][0] - CLICK[0] / 172.0) < 1.5]
    # 找不到就用"最新放置"的启发:与目标距离最近且未被占用的两脚件
    if not new:
        print(f"!! {name} no new inst")
        continue
    ni = min(new, key=lambda i: (i["loc"][0] - tx) ** 2 + (i["loc"][1] - ty) ** 2)
    if rot:
        s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orSetRot {ni["id"]} {rot}', 60)
        time.sleep(0.2)
    s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orSetLoc {ni["id"]} {tx} {ty}; orSetRef {ni["id"]} {name}', 60)
    time.sleep(0.2)
    print(f"{name}: id={ni['id']} -> ({tx},{ty})")

# ---- 复制 VDC(SNUBBER 页上自带 2 只)→ Vcc ----
print(s.eval(dx.SETUP_TCL + SET_ROT_HELPER + r'''
proc orCopyVdc { tx ty ref } {
    set st [DboState]
    set it [$::gExpSession NewDesignsIter $st]
    set d [$it NextDesign $st]
    set null NULL
    set src NULL
    set mypg NULL
    set sch [$d GetSchematic [orCStr {SCHEMATIC1}] $st]
    set mypg [$sch GetPage [orCStr {PAGE1}] $st]
    # 从设计其它页(RC/RLC/RL)找 VDC(source 库)
    set vit [$d NewViewsIter $st $::IterDefs_SCHEMATICS]
    set v [$vit NextView $st]
    while { $v != $null && $src == "NULL" } {
        set s2 [DboViewToDboSchematic $v]
        if { $s2 != $null } {
            set sn [DboTclHelper_sMakeCString]
            catch { $s2 GetName $sn }
            if { ! [string equal -nocase SCHEMATIC1 [DboTclHelper_sGetConstCharPtr $sn]] } {
                set pit [$s2 NewPagesIter $st]
                set p [$pit NextPage $st]
                set iit [$p NewPartInstsIter $st]
                set i [$iit NextPartInst $st]
                while { $i != $null && $src == "NULL" } {
                    set pl [DboPartInstToDboPlacedInst $i]
                    if { $pl != $null } {
                        set lib "?"
                        catch { set c [DboTclHelper_sMakeCString]; $pl GetSourceLibName $c; set lib [DboTclHelper_sGetConstCharPtr $c] }
                        if { [string match -nocase *source* $lib] } { set src $pl }
                    }
                    set i [$iit NextPartInst $st]
                }
                catch { delete_DboPagePartInstsIter $iit }
            }
        }
        set v [$vit NextView $st]
    }
    catch { delete_DboLibViewsIter $vit }
    if { $src == "NULL" } { error "no VDC found" }
    set ni [$mypg NewPlacedInst $src $st [DboTclHelper_sMakeCPoint 100 100]]
    set nid [$ni GetId $st]
    $ni SetEffectivePropStringValue [orCStr "Reference"] [orCStr $ref]
    $ni SetLocation [DboTclHelper_sMakeCPoint [expr { int($tx * 100) }] [expr { int($ty * 100) }]]
    return $nid
}
orCopyVdc 8.5 2.8 Vcc
''', 300))

# ---- 剪贴板粘贴 VSIN(accircuits 设计的 V1)→ Vs ----
import win32gui, win32con, win32api
frame = win32gui.FindWindow("OrCaptureFrame", None)
print("open acc:", s.eval(r'Open {C:\OrCAD\OrCAD_16.6_Lite\tools\capture\tclscripts\caplearningresources\hybrid\supportfiles\BasicElectronics\accircuits\designfiles\accircuits.dsn}', timeout=300))
time.sleep(4)
# 定位 accircuits 的 V1 所在页窗口并激活:通过 NPage 直接开
print("npage:", s.eval('if { [catch { NPage {rc} {PAGE1} } e] } { return "ERR: $e" } ; return "ok"', 120))
time.sleep(2)
# V1 在 rc/PAGE1 上:用 SelectObjectById 选中(copy 需要选中态)。
# id 已知策略失效(每次会话 id 变),改为:选中该页所有 source 库元件 → 先全选再复制也可(页面只有3个件)
print(s.eval(dx.SETUP_TCL + r'''
set pg [GetActivePage]
set st [DboState]
set out {}
set iit [$pg NewPartInstsIter $st]
set i [$iit NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $null } {
        set lib "?"
        catch { set c [DboTclHelper_sMakeCString]; $pl GetSourceLibName $c; set lib [DboTclHelper_sGetConstCharPtr $c] }
        if { [string match -nocase *source* $lib] } {
            set id [$pl GetId $st]
            SelectObjectById $id
            lappend out "selected V inst id=$id"
            break
        }
    }
    set i [$iit NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $iit }
return $out
''', 120))
print("copy:", s.eval('Copy()', 60))
time.sleep(0.5)
# 切回我的页面
print("close acc:", s.eval('if { [catch { CloseProject } e] } { return "ERR: $e" } ; return "closed"', 180))
time.sleep(2)
print("sel:", s.eval('SelectPMItem {PAGE1}', 60))
try:
    win32gui.SetForegroundWindow(frame)
except Exception:
    pass
time.sleep(0.5)
win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(3)
# 粘贴到 Vs 位置
print("paste:", s.eval('if { [catch { Paste 1.0 6.4 } e] } { return "ERR: $e" } ; return "ok"', 120))
time.sleep(1)
print(s.eval(dx.SETUP_TCL + SET_ROT_HELPER + r'''
set pg [GetActivePage]
set st [DboState]
set out {}
set iit [$pg NewPartInstsIter $st]
set i [$iit NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $null } {
        set rn "?"
        catch { set c [DboTclHelper_sMakeCString]; $pl GetReference $c; set rn [DboTclHelper_sGetConstCharPtr $c] }
        set lib "?"
        catch { set c2 [DboTclHelper_sMakeCString]; $pl GetSourceLibName $c2; set lib [string range [DboTclHelper_sGetConstCharPtr $c2] end-12 end] }
        set lc [$pl GetLocation $st]
        lappend out "$rn($lib)@[DboTclHelper_sGetCPointX $lc],[DboTclHelper_sGetCPointY $lc]"
    }
    set i [$iit NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $iit }
return $out
''', 180))
