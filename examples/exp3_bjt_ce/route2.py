"""实验3布线执行(镜像布局,y向下):导线/结点/地/别名/文本 + 引脚连通验证."""
import sys, os, time, json
sys.path.insert(0, ".")
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
from build_exp3 import parse_insts, SET_ROT_HELPER

dx.ensure_capture()
s = br.BRIDGE.session()
CAPSYM = dx.CAPSYM

# 1) 读取全部引脚真实页面坐标(GetOffsetHotSpot)
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
print("pins:", {k: v for k, v in PINS.items()})
json.dump(PINS, open("pins.json", "w", encoding="utf-8"), indent=1)

# 2) 布线(以实测引脚坐标为准)
W = []


def wire(p1, p2):
    W.append((p1, p2))


# Vs+ (1.1,6.3) → Rs1 (2.1,6.4)
wire(PINS["Vs"]["+"], (1.1, 6.0)); wire((1.1, 6.0), (2.0, 6.0))
wire((2.0, 6.0), (2.0, PINS["Rs"]["1"][1])); wire((2.0, PINS["Rs"]["1"][1]), PINS["Rs"]["1"])
# Rs2 → C1 (Vi)
wire(PINS["Rs"]["2"], PINS["C1"]["1"])
# C1 → 基极节点(y=6.2) → Q1 b
c12 = (PINS["C1"]["2"][0] + 0.1, PINS["C1"]["2"][1])
wire(PINS["C1"]["2"], c12); wire(c12, (c12[0], 6.2)); wire((c12[0], 6.2), PINS["Q1"]["b"])
# Rb1 上 → Vcc 母线(y=3.6); Rb1 下 → 基极母线
wire(PINS["Rb1"]["1"], (PINS["Rb1"]["1"][0], 3.6))
wire(PINS["Rb1"]["2"], (PINS["Rb1"]["2"][0], 6.2))
# Rb2 上 → 基极母线
wire(PINS["Rb2"]["1"], (PINS["Rb2"]["1"][0], 6.2))
# Vcc 母线 + 电池
wire((4.5, 3.6), (8.6, 3.6))
wire(PINS["Rc"]["1"], (PINS["Rc"]["1"][0], 3.6))
wire((8.6, 3.6), PINS["Vcc"]["+"])
# Rc 下 → 集电极节点(y=5.4) → Q1 c / C2
wire(PINS["Rc"]["2"], (PINS["Rc"]["2"][0], 5.4))
wire((5.5, 5.4), (7.2, 5.4))
wire((5.5, 5.4), PINS["Q1"]["c"])
wire((7.2, 5.4), PINS["C2"]["1"])
# 发射极节点(y=6.6) → Re / Ce
wire(PINS["Q1"]["e"], (PINS["Q1"]["e"][0], 6.6))
wire((5.5, 6.6), (7.8, 6.6))
wire(PINS["Re"]["1"], (PINS["Re"]["1"][0], 6.6))
wire(PINS["Ce"]["1"], (PINS["Ce"]["1"][0], 6.6))
# C2 → Vo → RL
wire(PINS["C2"]["2"], (PINS["C2"]["2"][0] + 1.7, PINS["C2"]["2"][1]))
wire((PINS["C2"]["2"][0] + 1.7, PINS["C2"]["2"][1]), PINS["RL"]["1"])

ok, fail = 0, []
for p1, p2 in W:
    cmd = f'PlaceWire {p1[0]} {p1[1]} {p2[0]} {p2[1]}'
    r = s.eval(f'if {{ [catch {{ {cmd} }} e] }} {{ return "ERR: $e" }} ; return "ok"', 60)
    if "ok" in r:
        ok += 1
    else:
        fail.append((cmd, r))
print(f"wires: {ok} ok, {len(fail)} fail")
for w, r in fail:
    print("  FAIL", w, r)

# 3) 结点
JUNCTIONS = [(4.5, 6.2), (4.5, 3.6), (6.6, 3.6), (6.6, 5.4), (6.8, 6.6)]
for jx, jy in JUNCTIONS:
    r = s.eval(f'if {{ [catch {{ PlaceJunction {jx} {jy} }} e] }} {{ return "ERR: $e" }} ; return "ok"', 60)
    print("junction", (jx, jy), r)

# 4) 地(直接放在引脚上)
GROUNDS = [PINS["Vs"]["-"], PINS["Rb2"]["2"], PINS["Re"]["2"], PINS["Ce"]["2"],
           PINS["RL"]["2"], PINS["Vcc"]["-"]]
for gx, gy in GROUNDS:
    r = s.eval(f'if {{ [catch {{ PlaceGround {gx} {gy} "{CAPSYM}" "GND_POWER" "0" }} e] }} {{ return "ERR: $e" }} ; return "ok"', 60)
    print("ground", (gx, gy), r)

# 5) 网络别名
vi_x = (PINS["Rs"]["2"][0] + PINS["C1"]["1"][0]) / 2
vo_x = PINS["C2"]["2"][0] + 0.9
for (ax_, ay), name in (((vi_x, PINS["Rs"]["2"][1]), "Vi"), ((vo_x, PINS["C2"]["2"][1]), "Vo")):
    r = s.eval(f'if {{ [catch {{ PlaceNetAlias {ax_} {ay} {name} }} e] }} {{ return "ERR: $e" }} ; return "ok"', 60)
    print("alias", name, r)

# 6) 班级姓名文本(页面上方)
r = s.eval('if { [catch { PlaceText 0.8 0.4 4.2 0.8 {班级:________  姓名:________} } e] } { return "ERR: $e" } ; return "ok"', 60)
print("text:", r)
print("done")
