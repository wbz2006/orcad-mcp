"""v3.1 认领堆叠件 + ID差集放置剩余 + VDC复制 + VSIN剪贴板."""
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE); sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
from build_exp3 import parse_insts, TCL_LIST_INSTS, SET_ROT_HELPER, find_click_point, click
import build_exp3

dx.ensure_capture()
s = br.BRIDGE.session()
CLICK = find_click_point()
build_exp3.CLICK_FIXED = CLICK
print("click:", CLICK)

def dump():
    return parse_insts(s.eval(dx.SETUP_TCL + SET_ROT_HELPER + TCL_LIST_INSTS, 120))

def fix(iid, tx, ty, ref, rot=0):
    if rot:
        s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orSetRot {iid} {rot}', 60)
        time.sleep(0.2)
    s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orSetLoc {iid} {tx} {ty}; orSetRef {iid} {ref}', 60)
    time.sleep(0.2)

# 1) 认领堆叠的 6 件
insts = dump()
stacked = [i for i in insts if abs(i["loc"][0] - 0.6) < 0.1]
rs = [i for i in stacked if len(i["pins"]) == 2 and i["ref"].startswith("R")]
cs = [i for i in stacked if len(i["pins"]) == 2 and i["ref"].startswith("C")]
assign = {}
for name, i in zip(("Rs", "Rb1", "Rc"), rs):
    assign[name] = i
for name, i in zip(("C1", "C2", "Ce"), cs):
    assign[name] = i
print("adopted:", {k: v["id"] for k, v in assign.items()})

LAYOUT = {
    "Rs": (2.2, 6.5, 0), "Rb1": (4.4, 4.8, 1), "Rc": (6.5, 4.8, 1),
    "C1": (3.4, 6.5, 0), "C2": (7.3, 4.5, 0), "Ce": (7.7, 7.0, 1),
    "Rb2": (4.4, 7.0, 1), "Re": (6.7, 7.0, 1), "RL": (9.1, 5.8, 1),
    "Q1": (5.4, 6.1, 0),
}
for name, i in assign.items():
    tx, ty, rot = LAYOUT[name]
    fix(i["id"], tx, ty, ref=name, rot=rot)
    print(f"{name}: fixed {i['id']} -> ({tx},{ty})")

# 2) ID差集放置剩余 3R + Q1
known = {i["id"] for i in dump()}
for name, lib, pkg in (
    ("Rb2", "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "R"),
    ("Re",  "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "R"),
    ("RL",  "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/analog.olb", "R"),
    ("Q1",  "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice/eval.olb",  "Q2N3904"),
):
    before = {i["id"] for i in dump()}
    s.eval(f'PlaceNew "{lib}" {pkg} 0', 60)
    time.sleep(0.3)
    click()
    s.eval('EndPlace; UnSelectAll', 60)
    time.sleep(0.4)
    after = dump()
    new = [i for i in after if i["id"] not in before and len(i["pins"]) == (3 if name == "Q1" else 2)]
    if not new:
        print(f"!! {name} no new inst")
        continue
    ni = new[0]
    tx, ty, rot = LAYOUT[name]
    fix(ni["id"], tx, ty, ref=name, rot=rot)
    known.add(ni["id"])
    assign[name] = ni
    print(f"{name}: placed id={ni['id']} -> ({tx},{ty})")

# 3) 复制 VDC → Vcc
r = s.eval(dx.SETUP_TCL + SET_ROT_HELPER + r'''
proc orCopyVdc2 { tx ty ref } {
    set st [DboState]
    set it [$::gExpSession NewDesignsIter $st]
    set d [$it NextDesign $st]
    set null NULL
    set src NULL
    set sch [$d GetSchematic [orCStr {SCHEMATIC1}] $st]
    set mypg [$sch GetPage [orCStr {PAGE1}] $st]
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
    if { $src == "NULL" } { error "no VDC" }
    set ni [$mypg NewPlacedInst $src $st [DboTclHelper_sMakeCPoint 100 100]]
    set nid [$ni GetId $st]
    $ni SetEffectivePropStringValue [orCStr "Reference"] [orCStr $ref]
    $ni SetLocation [DboTclHelper_sMakeCPoint [expr { int($tx * 100) }] [expr { int($ty * 100) }]]
    return $nid
}
orCopyVdc2 8.5 2.8 Vcc
''', 300)
print("Vcc copy:", r)
time.sleep(0.3)

# 4) VSIN 剪贴板:开 accircuits → 找 V1 页 → 选中 → Copy → 回来 Paste
print("open acc:", s.eval(r'Open {C:\OrCAD\OrCAD_16.6_Lite\tools\capture\tclscripts\caplearningresources\hybrid\supportfiles\BasicElectronics\accircuits\designfiles\accircuits.dsn}', timeout=300))
time.sleep(4)
# 枚举 accircuits 的原理图/页名
names = s.eval(dx.SETUP_TCL + r'''
set st [DboState]
set out {}
set it [$::gExpSession NewDesignsIter $st]
set d [$it NextDesign $st]
set null NULL
while { $d != $null } {
    set dn [DboTclHelper_sMakeCString]
    catch { $d GetName $dn }
    if { [string match -nocase *accircuits* [DboTclHelper_sGetConstCharPtr $dn]] } {
        set vit [$d NewViewsIter $st $::IterDefs_SCHEMATICS]
        set v [$vit NextView $st]
        while { $v != $null } {
            set s2 [DboViewToDboSchematic $v]
            if { $s2 != $null } {
                set sn [DboTclHelper_sMakeCString]
                catch { $s2 GetName $sn }
                set pit [$s2 NewPagesIter $st]
                set p [$pit NextPage $st]
                set pn [DboTclHelper_sMakeCString]
                catch { $p GetName $pn }
                lappend out "[DboTclHelper_sGetConstCharPtr $sn]/[DboTclHelper_sGetConstCharPtr $pn]"
            }
            set v [$vit NextView $st]
        }
        catch { delete_DboLibViewsIter $vit }
    }
    set d [$it NextDesign $st]
}
return $out
''', 120)
print("acc pages:", names)
