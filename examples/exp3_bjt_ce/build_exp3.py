"""实验3主构建脚本:重置底图 → 放置元件 → 查询引脚 → 连线 → 属性 → 保存。

用法: python build_exp3.py <stage>
  reset    - 杀Capture、拷贝干净ABC.DSN、生成极简opj、开工程、建SCHEMATIC1+PAGE1+SetRoot、开页面
  place    - 放置全部12个元件(点击提交+SetRotation+Move定位),输出 pins.json
  route    - 依据 pins.json 与本文件的 NETLIST 连接表画线、打结点、放电源地/别名/文本
  props    - 设置元件值与显示
  save     - File::Save 保存并验证
  verify   - 输出全页清单
"""

import json
import os
import shutil
import subprocess
import sys
import time

os.environ.setdefault("ORCAD_MCP_PORT", "5178")  # 必须在 import bridge 之前

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge as br  # noqa: E402
import draw_exp3 as dx  # noqa: E402  (复用 SETUP_TCL / ensure_capture / reaper)
import exp3lib  # noqa: E402

PROJ = exp3lib.PROJ_DIR
DSN = os.path.join(PROJ, "exp3.dsn").replace("\\", "/")
PSP = dx.PSP
CAPSYM = dx.CAPSYM

# 元件定义: name, lib, pkg, device, rot, 目标位置(英寸, 元件 origin)
# Capture 页面坐标 y 向下:Vcc 侧用小 y(上方), 地侧用大 y(下方)
PARTS = [
    # name   lib                    pkg        device     rot  tx    ty
    ("Vs",   f"{PSP}/source.olb",  "VSIN",    "VSIN",    0,   1.0,  6.4),
    ("Rs",   f"{PSP}/analog.olb",  "R",       "R",       0,   2.2,  6.5),
    ("C1",   f"{PSP}/analog.olb",  "C",       "C",       0,   3.4,  6.5),
    ("Rb1",  f"{PSP}/analog.olb",  "R",       "R",       1,   4.4,  4.8),
    ("Rc",   f"{PSP}/analog.olb",  "R",       "R",       1,   6.5,  4.8),
    ("Rb2",  f"{PSP}/analog.olb",  "R",       "R",       1,   4.4,  7.0),
    ("Q1",   f"{PSP}/eval.olb",    "Q2N3904", "Q2N3904", 0,   5.4,  6.1),
    ("Re",   f"{PSP}/analog.olb",  "R",       "R",       1,   6.7,  7.0),
    ("Ce",   f"{PSP}/analog.olb",  "C",       "C",       1,   7.7,  7.0),
    ("C2",   f"{PSP}/analog.olb",  "C",       "C",       0,   7.3,  4.5),
    ("RL",   f"{PSP}/analog.olb",  "R",       "R",       1,   9.1,  5.8),
    ("Vcc",  f"{PSP}/source.olb",  "VDC",     "VDC",     0,   8.5,  2.8),
]

PROPS = {
    "Vs":  [("VOFF", "0"), ("VAMPL", "5mV"), ("FREQ", "1kHz")],
    "Rs":  [("VALUE", "1k")],
    "C1":  [("VALUE", "10u")],
    "Rb1": [("VALUE", "57k")],
    "Rc":  [("VALUE", "2k")],
    "Rb2": [("VALUE", "30k")],
    "Re":  [("VALUE", "1k")],
    "Ce":  [("VALUE", "47u")],
    "C2":  [("VALUE", "10u")],
    "RL":  [("VALUE", "2k")],
    "Vcc": [("DC", "12V")],
}

CLICK_FIXED = None  # 由 find_click_point 决定


def find_click_point():
    """返回页面视图中心屏幕坐标(固定的提交点击点)."""
    import win32gui
    frame = win32gui.FindWindow("OrCaptureFrame", None)
    win32gui.SetForegroundWindow(frame)
    time.sleep(0.4)
    mdi = win32gui.FindWindowEx(frame, 0, "MDIClient", None)
    rects = []

    def cb(hwnd, acc):
        cls = win32gui.GetClassName(hwnd)
        if "AfxFrameOrView" in cls or "Afx:" in cls:
            r = win32gui.GetWindowRect(hwnd)
            if (r[2] - r[0]) > 300 and (r[3] - r[1]) > 300:
                acc.append(r)
        return True
    if mdi:
        import win32gui as w
        w.EnumChildWindows(mdi, cb, rects)
    r = rects[0] if rects else win32gui.GetWindowRect(frame)
    return (r[0] + r[2]) // 2, (r[1] + r[3]) // 2


def click():
    import win32api
    import win32con
    x, y = CLICK_FIXED
    win32api.SetCursorPos((x, y))
    time.sleep(0.15)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.1)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.3)


TCL_LIST_INSTS = r'''
set pg [GetActivePage]
set st [DboState]
set out {}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $null } {
        set id [$pl GetId $st]
        set rn "?"
        catch { set c [DboTclHelper_sMakeCString]; $pl GetReference $c; set rn [DboTclHelper_sGetConstCharPtr $c] }
        set lc [$pl GetLocation $st]
        set pins {}
        set pit [$pl NewPinsIter $st]
        set pin [$pit NextPin $st]
        while { $pin != $null } {
            set pn "?"
            catch { set c2 [DboTclHelper_sMakeCString]; $pin GetPinName $c2; set pn [DboTclHelper_sGetConstCharPtr $c2] }
            set sp [$pin GetStartPoint $st]
            set sx [DboTclHelper_sGetCPointX $sp]
            set sy [DboTclHelper_sGetCPointY $sp]
            set pp "?"
            catch {
                set ppv [$pin GetPinPosition $st]
                set pp "[DboTclHelper_sGetCPointX $ppv],[DboTclHelper_sGetCPointY $ppv]"
            }
            lappend pins "$pn|$sx,$sy|$pp"
            set pin [$pit NextPin $st]
        }
        catch { delete_DboPartInstPinsIter $pit }
        lappend out "$id|$rn|[DboTclHelper_sGetCPointX $lc],[DboTclHelper_sGetCPointY $lc]|[concat $pins]"
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
'''


def parse_insts(raw):
    insts = []
    for item in raw.split("} {"):
        t = item.strip("{}")
        f = t.split("|")
        if len(f) < 3:
            continue
        iid, ref, loc = f[0].strip(), f[1], f[2]
        pins = {}
        pinstr = t.split("|", 3)[3] if "|" in t else ""
        for pm in pinstr.split(" "):
            if "|" in pm:
                parts2 = pm.split("|")
                n, xy = parts2[0], parts2[1]
                x, y = xy.split(",")
                entry = {"off": (int(x) / 100.0, int(y) / 100.0)}
                if len(parts2) > 2 and "," in parts2[2]:
                    px, py = parts2[2].split(",")
                    if px not in ("?", ""):
                        entry["pos"] = (int(px) / 100.0, int(py) / 100.0)
                pins[n] = entry
        lx, ly = loc.split(",")
        insts.append({"id": iid, "ref": ref, "loc": (int(lx) / 100.0, int(ly) / 100.0), "pins": pins})
    return insts


def stage_reset() -> None:
    subprocess.run(["taskkill", "/F", "/IM", "Capture.exe"], capture_output=True)
    time.sleep(2)
    # accircuits 设计含 VSIN 实例(PlaceNew 对 source.olb 失效,复制是唯一来源)
    shutil.copyfile(r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\tclscripts\caplearningresources"
                    r"\hybrid\supportfiles\BasicElectronics\accircuits\designfiles\accircuits.dsn",
                    DSN.replace("/", "\\"))
    # 极简 opj(无 profile,注入 4 个符号库)
    import re
    opj = exp3lib.make_opj(None)
    opj = re.sub(r'\(File\.PSpice\.\{[0-9A-Fa-f-]+\}.*?\(Type "PSpice Profile"\)\)\n', "", opj, flags=re.S)
    opj = re.sub(r'\(File "[^"]*q2n3904_bf70\.lib"\s*\n\s*\(Type "PSpice Library"\)\)\n', "", opj)
    libs = "".join(
        f'    (File "C:\\\\OrCAD\\\\OrCAD_16.6_Lite\\\\tools\\\\capture\\\\library\\\\pspice\\\\{n}.olb"\n      (Type "Schematic Library"))\n'
        for n in ("analog", "source", "eval"))
    libs += '    (File "C:\\\\OrCAD\\\\OrCAD_16.6_Lite\\\\tools\\\\capture\\\\library\\\\capsym.olb"\n      (Type "Schematic Library"))\n'
    opj = opj.replace('    (Folder "Library")\n', '    (Folder "Library")\n' + libs)
    open(os.path.join(PROJ, "exp3.opj"), "w", encoding="latin-1").write(opj)
    dx.ensure_capture()
    s = br.BRIDGE.session()
    print("open:", s.eval(r'Open {D:\Users\Download\exp3_BJT_CE\exp3.opj}', timeout=300))
    time.sleep(3)
    print(s.eval(dx.SETUP_TCL + r'''
set _st [DboState]
set it [$::gExpSession NewDesignsIter $_st]
set _d [$it NextDesign $_st]
if { $_d == "NULL" } { error "no design" }
set sch [$_d NewSchematic [orCStr {SCHEMATIC1}] $_st]
if { $sch == "NULL" } { error "NewSchematic failed" }
set pg [$sch NewPage $_st [orCStr {PAGE1}]]
if { $pg == "NULL" } { error "NewPage failed" }
$_d SetRoot $sch
return "SCHEMATIC1/PAGE1 created, root set"
''', 180))
    print("save:", s.eval('Menu "File::Save"', timeout=180))
    time.sleep(2)
    print("close:", s.eval('CloseProject', timeout=120))
    time.sleep(2)
    print("reopen:", s.eval(r'Open {D:\Users\Download\exp3_BJT_CE\exp3.opj}', timeout=300))
    time.sleep(4)
    print("select:", s.eval('SelectPMItem {SCHEMATIC1}', timeout=60))
    print("npage:", s.eval('NPage {SCHEMATIC1} {PAGE1}', timeout=120))
    print("select page:", s.eval('SelectPMItem {PAGE1}', timeout=60))
    import win32gui
    import win32con
    import win32api
    frame = win32gui.FindWindow("OrCaptureFrame", None)
    win32gui.SetForegroundWindow(frame)
    time.sleep(0.5)
    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(3)
    print(s.eval(dx.SETUP_TCL + r'''
set pg [GetActivePage]
if { $pg == "NULL" || $pg == "" } { error "no active page" }
set nm [DboTclHelper_sMakeCString]
catch { $pg GetName $nm }
return "active page: [DboTclHelper_sGetConstCharPtr $nm]"
''', 60))


SET_ROT_HELPER = r'''
proc orSetLoc { id tx ty } {
    set pg [GetActivePage]
    set st [DboState]
    set it [$pg NewPartInstsIter $st]
    set i [$it NextPartInst $st]
    set null NULL
    while { $i != $null } {
        set pl [DboPartInstToDboPlacedInst $i]
        if { $pl != $null } {
            if { [$pl GetId $st] == $id } {
                $pl SetLocation [DboTclHelper_sMakeCPoint [expr { int($tx * 100) }] [expr { int($ty * 100) }]]
                return ok
            }
        }
        set i [$it NextPartInst $st]
    }
    error "inst $id not found"
}
proc orSetRot { id rot } {
    set pg [GetActivePage]
    set st [DboState]
    set it [$pg NewPartInstsIter $st]
    set i [$it NextPartInst $st]
    set null NULL
    while { $i != $null } {
        set pl [DboPartInstToDboPlacedInst $i]
        if { $pl != $null } {
            if { [$pl GetId $st] == $id } { $pl SetRotation $rot; return ok }
        }
        set i [$it NextPartInst $st]
    }
    error "inst $id not found"
}
proc orMoveTo { id tx ty } {
    set pg [GetActivePage]
    set st [DboState]
    set it [$pg NewPartInstsIter $st]
    set i [$it NextPartInst $st]
    set null NULL
    while { $i != $null } {
        set pl [DboPartInstToDboPlacedInst $i]
        if { $pl != $null } {
            if { [$pl GetId $st] == $id } {
                set lc [$pl GetLocation $st]
                set dx [expr { double([DboTclHelper_sGetCPointX $lc]) / 100.0 }]
                set dy [expr { double([DboTclHelper_sGetCPointY $lc]) / 100.0 }]
                if { [expr { abs($tx - $dx) }] > 0.001 || [expr { abs($ty - $dy) }] > 0.001 } {
                    SelectObjectById $id
                    Move [expr { $tx - $dx }] [expr { $ty - $dy }] 0
                    UnSelectAll
                }
                return "[DboTclHelper_sGetCPointX $lc],[DboTclHelper_sGetCPointY $lc]"
            }
        }
        set i [$it NextPartInst $st]
    }
    error "inst $id not found"
}
proc orSetRef { id ref } {
    set pg [GetActivePage]
    set st [DboState]
    set it [$pg NewPartInstsIter $st]
    set i [$it NextPartInst $st]
    set null NULL
    while { $i != $null } {
        set pl [DboPartInstToDboPlacedInst $i]
        if { $pl != $null } {
            if { [$pl GetId $st] == $id } {
                $pl SetEffectivePropStringValue [orCStr "Reference"] [orCStr $ref]
                return ok
            }
        }
        set i [$it NextPartInst $st]
    }
    error "inst $id not found"
}
'''


def stage_place() -> None:
    dx.ensure_capture()
    s = br.BRIDGE.session()
    global CLICK_FIXED
    CLICK_FIXED = find_click_point()
    print("click point:", CLICK_FIXED)
    insts = parse_insts(s.eval(dx.SETUP_TCL + SET_ROT_HELPER + TCL_LIST_INSTS, 120))
    claimed = {i["id"] for i in insts if i["loc"][1] < 2.0}  # 底图 rc/rl/rlc 页不管;本页初始为空
    claimed = set()
    result = {}
    for name, lib, pkg, dev, rot, tx, ty in PARTS:
        if name in ("Vs", "Vcc"):
            continue  # 稍后从底图页复制 VSIN
        ni = None
        for i in insts:
            if i["id"] in claimed:
                continue
            if abs(i["loc"][0] - tx) < 0.05 and abs(i["loc"][1] - ty) < 0.05 and len(i["pins"]) == (3 if name == "Q1" else 2):
                ni = i
                claimed.add(i["id"])
                print(f"{name}: adopted id={ni['id']} at target")
                break
        if ni is None:
            s.eval(f'PlaceNew "{lib}" {pkg} 0', 60)
            time.sleep(0.3)
            click()
            s.eval('EndPlace; UnSelectAll', 60)
            time.sleep(0.4)
            insts = parse_insts(s.eval(dx.SETUP_TCL + SET_ROT_HELPER + TCL_LIST_INSTS, 120))
            new = [i for i in insts if i["id"] not in claimed
                   and len(i["pins"]) == (3 if name == "Q1" else 2)
                   and abs(i["loc"][0] - 0.6) < 0.3]
            if not new:
                print(f"!! {name}: no new instance appeared")
                continue
            ni = new[-1]
        claimed.add(ni["id"])
        if rot:
            s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orSetRot {ni["id"]} {rot}', 60)
            time.sleep(0.25)
        s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orSetLoc {ni["id"]} {tx} {ty}', 60)
        time.sleep(0.25)
        s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orSetRef {ni["id"]} {name}', 60)
        time.sleep(0.15)
        insts = parse_insts(s.eval(dx.SETUP_TCL + SET_ROT_HELPER + TCL_LIST_INSTS, 120))
        ni = next(i for i in insts if i["id"] == ni["id"])
        result[name] = ni
        print(f"{name}: id={ni['id']} loc={ni['loc']}")

    # 复制两只 VSIN 作为 Vs / Vcc(source.olb 无法 PlaceNew,同设计复制已验证)
    s.eval(dx.SETUP_TCL + SET_ROT_HELPER + r'''
proc orCopyVsin { tx ty ref } {
    set _st [DboState]
    set dit [$::gExpSession NewDesignsIter $_st]
    set d [$dit NextDesign $_st]
    set null NULL
    set src NULL
    set srcpg NULL
    while { $d != $null } {
        set dn [DboTclHelper_sMakeCString]
        catch { $d GetName $dn }
        if { [string match -nocase *exp3* [DboTclHelper_sGetConstCharPtr $dn]] } {
            set vit [$d NewViewsIter $_st $::IterDefs_SCHEMATICS]
            set v [$vit NextView $_st]
            set sch [DboViewToDboSchematic $v]
            set pit [$sch NewPagesIter $_st]
            set srcpg [$pit NextPage $_st]
            set iit [$srcpg NewPartInstsIter $_st]
            set i [$iit NextPartInst $_st]
            while { $i != $null } {
                set pl [DboPartInstToDboPlacedInst $i]
                if { $pl != $null } {
                    set lib "?"
                    catch { set c [DboTclHelper_sMakeCString]; $pl GetSourceLibName $c; set lib [DboTclHelper_sGetConstCharPtr $c] }
                    if { [string match -nocase *source* $lib] } { set src $pl; break }
                }
                set i [$iit NextPartInst $_st]
            }
            catch { delete_DboPagePartInstsIter $iit }
        }
        set d [$dit NextDesign $_st]
    }
    if { $src == "NULL" } { error "no VSIN in design" }
    set ni [$srcpg NewPlacedInst $src $_st [DboTclHelper_sMakeCPoint [expr { int($tx * 100) }] [expr { int($ty * 100) }]]]
    set nid [$ni GetId $_st]
    $ni SetEffectivePropStringValue [orCStr "Reference"] [orCStr $ref]
    return $nid
}
''', 120)
    for ref, tx, ty in (("Vs", 1.0, 6.4), ("Vcc", 8.5, 2.8)):
        r = s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orCopyVsin {tx} {ty} {ref}', 120)
        print(f"copy {ref}: id={r}")
        time.sleep(0.3)

    insts = parse_insts(s.eval(dx.SETUP_TCL + SET_ROT_HELPER + TCL_LIST_INSTS, 120))
    for name, lib, pkg, dev, rot, tx, ty in PARTS:
        match = [i for i in insts if abs(i["loc"][0] - tx) < 0.03 and abs(i["loc"][1] - ty) < 0.03
                 and len(i["pins"]) == (3 if name == "Q1" else 2)]
        if match:
            result[name] = match[0]
        else:
            print(f"!! {name} not at target")
    with open("pins.json", "w", encoding="utf-8") as f:
        json.dump({k: v["pins"] for k, v in result.items()}, f, indent=1)
    print("pins.json written (flat: {ref: {pin: (x,y) 英寸}})")


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "reset"
    globals()[f"stage_{stage}"]()
    print(f"[stage {stage}] done")
