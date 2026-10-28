"""v4 最终重建:ABC 正常页底图 + 全禁缩放 + 完整电路 + 保存.
关键:绝不调用 ZoomScale/ZoomArea/ZoomAll/ZoomSelection(会毒化视图渲染).
"""
import sys, os, time, subprocess, shutil, json
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE); sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx, exp3lib
from build_exp3 import parse_insts, TCL_LIST_INSTS, SET_ROT_HELPER, find_click_point, click
import build_exp3

PSP = "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice"
CAPSYM = "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/capsym.olb"
PROJ = r"D:\Users\Download\exp3_BJT_CE"

subprocess.run(["taskkill", "/F", "/IM", "Capture.exe"], capture_output=True)
time.sleep(2)
dx.ensure_capture()
s = br.BRIDGE.session()
shutil.copyfile(r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\samples\Demo\ABC.DSN",
                os.path.join(PROJ, "EXP3.DSN"))
opj = exp3lib.make_opj(None)
libs = "".join(
    '    (File "C:\\\\OrCAD\\\\OrCAD_16.6_Lite\\\\tools\\\\capture\\\\library\\\\pspice\\\\' + n + '.olb"\n      (Type "Schematic Library"))\n'
    for n in ("analog", "source", "eval"))
libs += '    (File "C:\\\\OrCAD\\\\OrCAD_16.6_Lite\\\\tools\\\\capture\\\\library\\\\capsym.olb"\n      (Type "Schematic Library"))\n'
opj = opj.replace('    (Folder "Library")\n', '    (Folder "Library")\n' + libs)
open(os.path.join(PROJ, "exp3.opj"), "w", encoding="latin-1").write(opj)

s.eval(r'Open {D:\Users\Download\exp3_BJT_CE\exp3.opj}', timeout=300)
time.sleep(4)
print(s.eval(dx.SETUP_TCL + r'''
set st [DboState]
set it [$::gExpSession NewDesignsIter $st]
set _d [$it NextDesign $st]
if { $_d == "NULL" } { error "no design" }
set sch [$_d NewSchematic [orCStr {SCHEMATIC1}] $st]
if { $sch == "NULL" } { set sch [$_d GetSchematic [orCStr {SCHEMATIC1}] $st] }
set pg [$sch NewPage $st [orCStr {PAGE1}]]
if { $pg == "NULL" } { set pg [$sch GetPage [orCStr {PAGE1}] $st] }
$_d SetRoot $sch
set w "?"; set h "?"
catch { set w [$pg GetPageWidth] }
catch { set h [$pg GetPageHeight] }
return "page ready $w x $h"
''', 180))
print("save:", s.eval('SelectPMItem {SCHEMATIC1}; Menu "File::Save"', 180))
time.sleep(2)
print("close:", s.eval('CloseProject', 180))
time.sleep(2)
print("reopen:", s.eval(r'Open {D:\Users\Download\exp3_BJT_CE\exp3.opj}', timeout=300))
time.sleep(4)
print("sel:", s.eval('SelectPMItem {PAGE1}', 60))
import win32gui, win32con, win32api
frame = win32gui.FindWindow("OrCaptureFrame", None)
try: win32gui.SetForegroundWindow(frame)
except Exception: pass
time.sleep(0.5)
win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(3)
CLICK = find_click_point()
build_exp3.CLICK_FIXED = CLICK
print("click:", CLICK)

def dump():
    return parse_insts(s.eval(dx.SETUP_TCL + SET_ROT_HELPER + TCL_LIST_INSTS, 120))

def fix(iid, tx, ty, ref, rot):
    if rot:
        s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orSetRot {iid} {rot}', 60)
        time.sleep(0.2)
    s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orSetLoc {iid} {tx} {ty}; orSetRef {iid} {ref}', 60)
    time.sleep(0.2)

# ---------- 2. 放元件(ID差集) ----------
LAYOUT = [
    ("Rs",  f"{PSP}/analog.olb", "R", 0, 2.2, 6.5), ("C1", f"{PSP}/analog.olb", "C", 0, 3.4, 6.5),
    ("Rb1", f"{PSP}/analog.olb", "R", 1, 4.4, 4.8), ("Rc", f"{PSP}/analog.olb", "R", 1, 6.5, 4.8),
    ("Rb2", f"{PSP}/analog.olb", "R", 1, 4.4, 7.0), ("Q1", f"{PSP}/eval.olb", "Q2N3904", 0, 5.4, 6.1),
    ("Re",  f"{PSP}/analog.olb", "R", 1, 6.7, 7.0), ("Ce", f"{PSP}/analog.olb", "C", 1, 7.7, 7.0),
    ("C2",  f"{PSP}/analog.olb", "C", 0, 7.3, 4.5), ("RL", f"{PSP}/analog.olb", "R", 1, 9.1, 5.8),
]
for name, lib, pkg, rot, tx, ty in LAYOUT:
    placed = False
    for attempt in range(3):
        before = {i["id"] for i in dump()}
        s.eval(f'PlaceNew "{lib}" {pkg} 0', 60)
        time.sleep(0.3)
        click()
        s.eval('EndPlace; UnSelectAll', 60)
        time.sleep(0.4)
        new = [i for i in dump() if i["id"] not in before and len(i["pins"]) == (3 if name == "Q1" else 2)]
        if new:
            ni = new[0]
            fix(ni["id"], tx, ty, name, rot)
            print(f"{name}: id={ni['id']}")
            placed = True
            break
        print(f"  {name} retry {attempt}")
    if not placed:
        print(f"!! {name} FAILED")

# ---------- 3. VSIN + VDC (source.olb,重试+全页检测) ----------
def try_source(pkg, tx, ty, ref, props):
    for attempt in range(3):
        before = {i["id"] for i in dump()}
        s.eval(f'PlaceNew "{PSP}/source.olb" {pkg} 0', 60)
        time.sleep(0.3)
        click()
        s.eval('EndPlace; UnSelectAll', 60)
        time.sleep(0.4)
        new = [i for i in dump() if i["id"] not in before and len(i["pins"]) == 2
               and abs(i["loc"][0] - tx) > 0.05]
        if new:
            ni = new[0]
            fix(ni["id"], tx, ty, ref, 0)
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
        if {{ [$pl GetId $st] == {ni["id"]} }} {{
            $pl SetEffectivePropStringValue [orCStr "{pn}"] [orCStr "{pv}"]
            return "ok"
        }}
    }}
    set i [$it NextPartInst $st]
}}
catch {{ delete_DboPagePartInstsIter $it }}
return "nf"
''', 60)
            print(f"{ref}: id={ni['id']} (attempt {attempt})")
            return True
        print(f"  {ref} retry {attempt}")
    return False

try_source("VSIN", 1.0, 6.4, "Vs", [("VOFF", "0"), ("VAMPL", "5mV"), ("FREQ", "1kHz")])
try_source("VDC", 8.5, 2.8, "Vcc", [("DC", "12V")])
print("save:", s.eval('Menu "File::Save"', 180))

# ---------- 4. 引脚坐标 + 布线 ----------
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
    if len(parts) < 2: continue
    ref = parts[0]; pins = {}
    for pm in parts[1].split(" "):
        if "|" in pm:
            n, xy = pm.split("|", 1)
            x, y = xy.split(",")
            pins[n] = (int(x) / 100.0, int(y) / 100.0)
    PINS[ref] = pins
json.dump(PINS, open("pins.json", "w", encoding="utf-8"), indent=1)
print("pins refs:", list(PINS))

def tb(name):
    p = PINS[name]
    top = p["1"] if p["1"][1] < p["2"][1] else p["2"]
    return top, (p["2"] if p["1"][1] < p["2"][1] else p["1"])

W = []
def wire(p1, p2): W.append((p1, p2))
wire(PINS["Vs"]["+"], (1.1, 6.0)); wire((1.1, 6.0), (2.0, 6.0))
wire((2.0, 6.0), (2.0, PINS["Rs"]["1"][1])); wire((2.0, PINS["Rs"]["1"][1]), PINS["Rs"]["1"])
wire(PINS["Rs"]["2"], PINS["C1"]["1"])
c12 = (PINS["C1"]["2"][0] + 0.1, PINS["C1"]["2"][1])
wire(PINS["C1"]["2"], c12); wire(c12, (c12[0], PINS["Q1"]["b"][1])); wire((c12[0], PINS["Q1"]["b"][1]), PINS["Q1"]["b"])
Rb1t, Rb1b = tb("Rb1"); Rb2t, Rb2b = tb("Rb2"); Rct, Rcb = tb("Rc")
Ret, Reb = tb("Re"); Cet, Ceb = tb("Ce"); RLt, RLb = tb("RL")
rail_y = PINS["Vcc"]["+"][1] + 0.9
baserail_y = PINS["Q1"]["b"][1]
col_y = PINS["Q1"]["c"][1] - 0.6
emit_y = PINS["Q1"]["e"][1] + 0.2
wire(Rb1t, (Rb1t[0], rail_y)); wire(Rb1b, (Rb1b[0], baserail_y))
wire(Rb2t, (Rb2t[0], baserail_y))
wire((Rb1t[0], rail_y), (8.6, rail_y)); wire(PINS["Rc"]["1"] if PINS["Rc"]["1"][1] < PINS["Rc"]["2"][1] else PINS["Rc"]["2"], (PINS["Rc"]["1"][0], rail_y))
wire((8.6, rail_y), PINS["Vcc"]["+"])
rc_bottom = PINS["Rc"]["2"] if PINS["Rc"]["1"][1] < PINS["Rc"]["2"][1] else PINS["Rc"]["1"]
wire(rc_bottom, (rc_bottom[0], col_y)); wire((5.5, col_y), (7.2, col_y))
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
print(f"wires {ok} ok {len(fail)} fail")
for f_ in fail: print("  FAIL", f_)

for jx, jy in ((Rb1b[0], baserail_y), (Rb1t[0], rail_y), (rc_bottom[0], rail_y), (rc_bottom[0], col_y), (Ret[0], emit_y)):
    s.eval(f'PlaceJunction {jx} {jy}', 60)
for gx, gy in (PINS["Vs"]["-"], Rb2b, Reb, Ceb, RLb, PINS["Vcc"]["-"]):
    s.eval(f'PlaceGround {gx} {gy} "{CAPSYM}" "GND_POWER" "0"', 60)
s.eval(f'PlaceNetAlias {(PINS["Rs"]["2"][0] + PINS["C1"]["1"][0]) / 2} {PINS["Rs"]["2"][1]} Vi', 60)
s.eval(f'PlaceNetAlias {PINS["C2"]["2"][0] + 0.9} {PINS["C2"]["2"][1]} Vo', 60)
s.eval('PlaceText 0.6 0.35 4.0 0.7 {班级:________  姓名:________}', 60)
PROPS = {"Vcc": [("DC", "12V")], "Vs": [("VOFF", "0"), ("VAMPL", "5mV"), ("FREQ", "1kHz")],
         "Rs": [("VALUE", "1k")], "C1": [("VALUE", "10u")], "Rb1": [("VALUE", "57k")],
         "Rc": [("VALUE", "2k")], "Rb2": [("VALUE", "30k")], "Re": [("VALUE", "1k")],
         "Ce": [("VALUE", "47u")], "C2": [("VALUE", "10u")], "RL": [("VALUE", "2k")]}
for ref, props in PROPS.items():
    if ref not in PINS: continue
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
return "nf {ref} {pn}"
''', 60)
print("save:", s.eval('Menu "File::Save"', 180))
print("V4 DONE — 全程无缩放命令")
