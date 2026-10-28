"""v5:安全区布局重建(全部元件/连线收进 11x8.5 页面,避开标题栏 6.5+/5.9+)."""
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
shutil.copyfile(r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\samples\Demo\ABC.DSN",
                os.path.join(PROJ, "EXP3.DSN"))
opj = exp3lib.make_opj(None)
libs = "".join(
    '    (File "C:\\\\OrCAD\\\\OrCAD_16.6_Lite\\\\tools\\\\capture\\\\library\\\\pspice\\\\' + n + '.olb"\n      (Type "Schematic Library"))\n'
    for n in ("analog", "source", "eval"))
libs += '    (File "C:\\\\OrCAD\\\\OrCAD_16.6_Lite\\\\tools\\\\capture\\\\library\\\\capsym.olb"\n      (Type "Schematic Library"))\n'
opj = opj.replace('    (Folder "Library")\n', '    (Folder "Library")\n' + libs)
open(os.path.join(PROJ, "exp3.opj"), "w", encoding="latin-1").write(opj)

dx.ensure_capture()
s = br.BRIDGE.session()
s.eval(r'Open {D:\Users\Download\exp3_BJT_CE\exp3.opj}', timeout=300)
time.sleep(4)
print(s.eval(dx.SETUP_TCL + r'''
set st [DboState]
set it [$::gExpSession NewDesignsIter $st]
set _d [$it NextDesign $st]
set sch [$_d NewSchematic [orCStr {SCHEMATIC1}] $st]
if { $sch == "NULL" } { set sch [$_d GetSchematic [orCStr {SCHEMATIC1}] $st] }
set pg [$sch NewPage $st [orCStr {PAGE1}]]
if { $pg == "NULL" } { set pg [$sch GetPage [orCStr {PAGE1}] $st] }
$_d SetRoot $sch
return "page ready"
''', 180))
s.eval('SelectPMItem {SCHEMATIC1}; Menu "File::Save"', 180)
time.sleep(2)
s.eval('CloseProject', 180)
time.sleep(2)
s.eval(r'Open {D:\Users\Download\exp3_BJT_CE\exp3.opj}', timeout=300)
time.sleep(4)
s.eval('SelectPMItem {PAGE1}', 60)
frame = win32gui = __import__("win32gui")
win32gui = frame and __import__("win32gui")
import win32gui as w32
frm = w32.FindWindow("OrCaptureFrame", None)
try: w32.SetForegroundWindow(frm)
except Exception: pass
time.sleep(0.5)
w32api = __import__("win32api")
w32api.keybd_event(0x0D, 0, 0, 0)
w32api.keybd_event(0x0D, 0, 2, 0)
time.sleep(3)

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

# 安全区布局(y 向下;避开标题栏 x>6.5 & y>5.9)
LAYOUT = [
    ("Vcc", f"{PSP}/source.olb", "VDC",     2, 0.9, 1.0),   # rot2: + 朝下接母线
    ("Rb1", f"{PSP}/analog.olb", "R",  1, 3.2, 2.5),
    ("Rc",  f"{PSP}/analog.olb", "R",  1, 5.4, 2.5),
    ("C2",  f"{PSP}/analog.olb", "C",  0, 6.3, 2.2),
    ("RL",  f"{PSP}/analog.olb", "R",  1, 8.3, 3.0),
    ("Q1",  f"{PSP}/eval.olb",  "Q2N3904", 0, 4.3, 3.8),
    ("Vs",  f"{PSP}/source.olb", "VSIN",   0, 0.8, 3.9),
    ("Rs",  f"{PSP}/analog.olb", "R",  0, 1.9, 4.3),
    ("C1",  f"{PSP}/analog.olb", "C",  0, 2.6, 4.3),
    ("Rb2", f"{PSP}/analog.olb", "R",  1, 3.2, 4.6),
    ("Re",  f"{PSP}/analog.olb", "R",  1, 5.6, 4.8),
    ("Ce",  f"{PSP}/analog.olb", "C",  1, 6.2, 4.8),
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
            fix(new[0]["id"], tx, ty, name, rot)
            print(f"{name}: id={new[0]['id']}")
            placed = True
            break
        print(f"  {name} retry {attempt}")
    if not placed:
        print(f"!! {name} FAILED")

# 属性
PROPS = {"Vcc": [("DC", "12V")], "Vs": [("VOFF", "0"), ("VAMPL", "5mV"), ("FREQ", "1kHz")],
         "Rs": [("VALUE", "1k")], "C1": [("VALUE", "10u")], "Rb1": [("VALUE", "57k")],
         "Rc": [("VALUE", "2k")], "Rb2": [("VALUE", "30k")], "Re": [("VALUE", "1k")],
         "Ce": [("VALUE", "47u")], "C2": [("VALUE", "10u")], "RL": [("VALUE", "2k")]}
for ref, props in PROPS.items():
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
return "nf"
''', 60)
print("props done")
print("save:", s.eval('Menu "File::Save"', 180))

# 引脚真坐标
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
print("PINS:", json.dumps(PINS))
