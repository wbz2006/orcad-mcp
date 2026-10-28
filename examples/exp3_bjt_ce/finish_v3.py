"""v3 收尾:VSIN跨设计复制 → 布线 → 地/结点/别名/文本 → 属性 → 保存 → ZoomAll."""
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE); sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
from build_exp3 import parse_insts, TCL_LIST_INSTS, SET_ROT_HELPER

dx.ensure_capture()
s = br.BRIDGE.session()

# 1) VSIN 跨设计复制(已验证 before/after 计数法)
print("open acc:", s.eval(r'Open {C:\OrCAD\OrCAD_16.6_Lite\tools\capture\tclscripts\caplearningresources\hybrid\supportfiles\BasicElectronics\accircuits\designfiles\accircuits.dsn}', timeout=300))
time.sleep(4)
r = s.eval(dx.SETUP_TCL + SET_ROT_HELPER + r'''
set st [DboState]
set dit [$::gExpSession NewDesignsIter $st]
set d [$dit NextDesign $st]
set null NULL
set src NULL
set mypg NULL
while { $d != $null } {
    set dn [DboTclHelper_sMakeCString]
    catch { $d GetName $dn }
    set isExp [string match -nocase *EXP3* [DboTclHelper_sGetConstCharPtr $dn]]
    set vit [$d NewViewsIter $st $::IterDefs_SCHEMATICS]
    set v [$vit NextView $st]
    while { $v != $null } {
        set s2 [DboViewToDboSchematic $v]
        if { $s2 != $null } {
            set sn [DboTclHelper_sMakeCString]
            catch { $s2 GetName $sn }
            set isSC1 [string equal -nocase SCHEMATIC1 [DboTclHelper_sGetConstCharPtr $sn]]
            set pit [$s2 NewPagesIter $st]
            set p [$pit NextPage $st]
            if { $isExp && $isSC1 } { set mypg $p }
            if { ! $isExp && $src == "NULL" } {
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
    set d [$dit NextDesign $st]
}
if { $src == "NULL" } { error "no src" }
if { $mypg == "NULL" } { error "no mypg" }
set ni [$mypg NewPlacedInst $src $st [DboTclHelper_sMakeCPoint 100 640]]
set nid [$ni GetId $st]
$ni SetEffectivePropStringValue [orCStr "Reference"] [orCStr "Vs"]
$ni SetLocation [DboTclHelper_sMakeCPoint 100 640]
return "vsin copied id=$nid"
''', 300)
print(r)
time.sleep(0.5)
print("close acc:", s.eval('if { [catch { CloseProject } e] } { return "ERR: $e" } ; return "closed"', 180))
time.sleep(2)

# 2) 激活我的页面
print("sel:", s.eval('SelectPMItem {PAGE1}', 60))
import win32gui, win32con, win32api
frame = win32gui.FindWindow("OrCaptureFrame", None)
try: win32gui.SetForegroundWindow(frame)
except Exception: pass
time.sleep(0.5)
win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(3)

# 3) 读引脚真坐标
raw = s.eval(dx.SETUP_TCL + SET_ROT_HELPER + r'''
set pg [GetActivePage]
set st [DboState]
set out {}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $null } {
        set rn "?"
        catch { set c [DboTclHelper_sMakeCString]; $pl GetReference $c; set rn [DboTclHelper_sGetConstCharPtr $c] }
        set pins {}
        set pit [$pl NewPinsIter $st]
        set pin [$pit NextPin $st]
        while { $pin != $null } {
            set pn "?"
            catch { set c2 [DboTclHelper_sMakeCString]; $pin GetPinName $c2; set pn [DboTclHelper_sGetConstCharPtr $c2] }
            set hs "?"
            catch { set hs [$pin GetOffsetHotSpot $st]; set hs "[DboTclHelper_sGetCPointX $hs],[DboTclHelper_sGetCPointY $hs]" }
            lappend pins "$pn|$hs"
            set pin [$pit NextPin $st]
        }
        catch { delete_DboPartInstPinsIter $pit }
        lappend out "$rn|[concat $pins]"
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return $out
''', 180)
PINS = {}
for item in raw.split("} {"):
    t = item.strip("{}")
    parts = t.split("|", 1)
    if len(parts) < 2:
        continue
    ref = parts[0]
    pins = {}
    for pm in parts[1].split(" "):
        if "|" in pm:
            n, xy = pm.split("|", 1)
            x, y = xy.split(",")
            pins[n] = (int(x) / 100.0, int(y) / 100.0)
    PINS[ref] = pins
print("pins:", json.dumps(PINS) if False else PINS)
import json
json.dump(PINS, open("pins.json", "w", encoding="utf-8"), indent=1)

# 4) 布线
W = []
def wire(p1, p2): W.append((p1, p2))
wire(PINS["Vs"]["+"], (1.1, 6.0)); wire((1.1, 6.0), (2.0, 6.0))
wire((2.0, 6.0), (2.0, PINS["Rs"]["1"][1])); wire((2.0, PINS["Rs"]["1"][1]), PINS["Rs"]["1"])
wire(PINS["Rs"]["2"], PINS["C1"]["1"])
c12 = (PINS["C1"]["2"][0] + 0.1, PINS["C1"]["2"][1])
wire(PINS["C1"]["2"], c12); wire(c12, (c12[0], PINS["Q1"]["b"][1])); wire((c12[0], PINS["Q1"]["b"][1]), PINS["Q1"]["b"])

def tb(name):
    p = PINS[name]
    top = p["1"] if p["1"][1] < p["2"][1] else p["2"]
    bot = p["2"] if p["1"][1] < p["2"][1] else p["1"]
    return top, bot

Rb1t, Rb1b = tb("Rb1"); Rb2t, Rb2b = tb("Rb2"); Rct, Rcb = tb("Rc")
Ret, Reb = tb("Re"); Cet, Ceb = tb("Ce"); RLt, RLb = tb("RL")
rail_y = PINS["Vcc"]["+"][1] + 0.9
baserail_y = PINS["Q1"]["b"][1]
col_y = PINS["Q1"]["c"][1] - 0.6
emit_y = PINS["Q1"]["e"][1] + 0.2
wire(Rb1t, (Rb1t[0], rail_y)); wire(Rb1b, (Rb1b[0], baserail_y))
wire(Rb2t, (Rb2t[0], baserail_y))
wire((Rb1t[0], rail_y), (8.6, rail_y)); wire(PINS["Rc"]["1"], (PINS["Rc"]["1"][0], rail_y))
wire((8.6, rail_y), PINS["Vcc"]["+"])
wire(Rcb, (Rcb[0], col_y)); wire((5.5, col_y), (7.2, col_y))
wire((5.5, col_y), PINS["Q1"]["c"]); wire((7.2, col_y), PINS["C2"]["1"])
wire(PINS["Q1"]["e"], (PINS["Q1"]["e"][0], emit_y)); wire((5.5, emit_y), (Cet[0], emit_y))
wire(Ret, (Ret[0], emit_y)); wire(Cet, (Cet[0], emit_y))
wire(PINS["C2"]["2"], (PINS["C2"]["2"][0] + 1.7, PINS["C2"]["2"][1]))
wire((PINS["C2"]["2"][0] + 1.7, PINS["C2"]["2"][1]), RLt)

ok, fail = 0, []
for p1, p2 in W:
    r = s.eval(f'if {{ [catch {{ PlaceWire {p1[0]} {p1[1]} {p2[0]} {p2[1]} }} e] }} {{ return "ERR: $e" }} ; return "ok"', 60)
    if "ok" in r: ok += 1
    else: fail.append((p1, p2, r))
print(f"wires {ok} ok, {len(fail)} fail")
for f_ in fail: print("  FAIL", f_)

# 5) 结点 / 地 / 别名 / 文本
for jx, jy in ((Rb1b[0], baserail_y), (Rb1t[0], rail_y), (Rct[0], rail_y),
               (Rcb[0], col_y), (Ret[0], emit_y)):
    r = s.eval(f'if {{ [catch {{ PlaceJunction {jx} {jy} }} e] }} {{ return "ERR: $e" }} ; return "ok"', 60)
    print("junction", (jx, jy), r)
for gx, gy in (PINS["Vs"]["-"], Rb2b, Reb, Ceb, RLb, PINS["Vcc"]["-"]):
    r = s.eval(f'if {{ [catch {{ PlaceGround {gx} {gy} "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/capsym.olb" "GND_POWER" "0" }} e] }} {{ return "ERR: $e" }} ; return "ok"', 60)
    print("ground", (gx, gy), r)
for (ax_, ay), nm in (((PINS["Rs"]["2"][0] + PINS["C1"]["1"][0]) / 2, PINS["Rs"]["2"][1]), ("Vi"),
                      ((PINS["C2"]["2"][0] + 0.9, PINS["C2"]["2"][1]), "Vo")):
    pass
r = s.eval(f'if {{ [catch {{ PlaceNetAlias {(PINS["Rs"]["2"][0] + PINS["C1"]["1"][0]) / 2} {PINS["Rs"]["2"][1]} Vi }} e] }} {{ return "ERR: $e" }} ; return "ok"', 60)
print("alias Vi:", r)
r = s.eval(f'if {{ [catch {{ PlaceNetAlias {PINS["C2"]["2"][0] + 0.9} {PINS["C2"]["2"][1]} Vo }} e] }} {{ return "ERR: $e" }} ; return "ok"', 60)
print("alias Vo:", r)
r = s.eval('if { [catch { PlaceText 0.8 0.4 4.2 0.75 {班级:________  姓名:________} } e] } { return "ERR: $e" } ; return "ok"', 60)
print("text:", r)

# 6) 元件值
PROPS = {"Vcc": [("DC", "12V")], "Vs": [("VOFF", "0"), ("VAMPL", "5mV"), ("FREQ", "1kHz")],
         "Rs": [("VALUE", "1k")], "C1": [("VALUE", "10u")], "Rb1": [("VALUE", "57k")],
         "Rc": [("VALUE", "2k")], "Rb2": [("VALUE", "30k")], "Re": [("VALUE", "1k")],
         "Ce": [("VALUE", "47u")], "C2": [("VALUE", "10u")], "RL": [("VALUE", "2k")]}
for ref, props in PROPS.items():
    if ref not in PINS:
        print(f"!! {ref} missing")
        continue
    for pn, pv in props:
        s.eval(dx.SETUP_TCL + f'''
set pg [GetActivePage]
set st [DboState]
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while {{ $i != $null }} {{
    set pl [DboPartInstToDboPlacedInst $i]
    if {{ $pl != $null }} {{
        set rn "?"
        catch {{ set c [DboTclHelper_sMakeCString]; $pl GetReference $c; set rn [DboTclHelper_sGetConstCharPtr $c] }}
        if {{ $rn eq "{ref}" }} {{
            $pl SetEffectivePropStringValue [orCStr "{pn}"] [orCStr "{pv}"]
            return "ok"
        }}
    }}
    set i [$it NextPartInst $st]
}}
catch {{ delete_DboPagePartInstsIter $it }}
return "REF NOT FOUND {ref}"
''', 60)
print("props done")

# 7) 保存 + ZoomAll(留好视图状态)
print("save:", s.eval('Menu "File::Save"', 180))
print("zoomall:", s.eval('ZoomAll', 60))
print("save2:", s.eval('Menu "File::Save"', 180))
print("ALL DONE")
