import sys, os, time, json
sys.path.insert(0, ".")
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
import build_exp3
from build_exp3 import find_click_point, click, parse_insts, TCL_LIST_INSTS

dx.ensure_capture()
s = br.BRIDGE.session()
CLICK = find_click_point()
build_exp3.CLICK_FIXED = CLICK
print("click:", CLICK)

SET_ROT_HELPER = r'''
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
                SelectObjectById $id
                Move [expr { $tx - $dx }] [expr { $ty - $dy }] 0
                UnSelectAll
                return ok
            }
        }
        set i [$it NextPartInst $st]
    }
    error "inst $id not found"
}
'''

def dump():
    return parse_insts(s.eval(dx.SETUP_TCL + SET_ROT_HELPER + TCL_LIST_INSTS, 120))

# 1) 修 Rb1(id=101): 旋转+移动+改名
s.eval(dx.SETUP_TCL + SET_ROT_HELPER + 'orSetRot 101 1; orMoveTo 101 4.4 3.2; orSetRef 101 Rb1', 120)
time.sleep(0.5)
# 2) 改 C1 的名(Rs 已改)
s.eval(dx.SETUP_TCL + SET_ROT_HELPER + 'orSetRef 76 C1', 60)

# 3) 放置其余元件
REST = [
    ("Vs",   f"{dx.PSP}/source.olb",  "VSIN.Normal", 0,   1.0,  1.6),
    ("Rc",   f"{dx.PSP}/analog.olb",  "R",           1,   6.5,  3.2),
    ("Rb2",  f"{dx.PSP}/analog.olb",  "R",           1,   4.4,  1.0),
    ("Q1",   f"{dx.PSP}/eval.olb",    "Q2N3904",     0,   5.4,  1.9),
    ("Re",   f"{dx.PSP}/analog.olb",  "R",           1,   6.7,  1.0),
    ("Ce",   f"{dx.PSP}/analog.olb",  "C",           1,   7.7,  1.0),
    ("C2",   f"{dx.PSP}/analog.olb",  "C",           0,   7.3,  3.5),
    ("RL",   f"{dx.PSP}/analog.olb",  "R",           1,   9.1,  2.2),
    ("Vcc",  f"{dx.PSP}/source.olb",  "VDC.Normal",  0,   8.5,  5.2),
]
known = {i["id"] for i in dump()}
placed = {i["ref"]: i for i in dump()}
for name, lib, pkg, rot, tx, ty in REST:
    s.eval(dx.SETUP_TCL + f'PlaceNew "{lib}" {pkg} 0', 60)
    time.sleep(0.3)
    click()
    s.eval('EndPlace; UnSelectAll', 60)
    time.sleep(0.4)
    insts = dump()
    new = [i for i in insts if i["id"] not in known]
    if not new:
        print(f"!! {name}: no new instance")
        continue
    ni = new[0]
    known.add(ni["id"])
    if rot:
        s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orSetRot {ni["id"]} {rot}', 60)
        time.sleep(0.3)
        insts = dump()
        ni = next(i for i in insts if i["id"] == ni["id"])
    s.eval(dx.SETUP_TCL + SET_ROT_HELPER + f'orMoveTo {ni["id"]} {tx} {ty}; orSetRef {ni["id"]} {name}', 120)
    time.sleep(0.4)
    insts = dump()
    ni = next(i for i in insts if i["id"] == ni["id"])
    placed[name] = ni
    print(f"{name}: id={ni['id']} loc={ni['loc']} pins={ni['pins']}")

# Rs 修正引用
if "Rs" not in placed:
    for i in dump():
        if i["id"] == "51":
            placed["Rs"] = i
# 最终 dump 按名字归档
final = {}
for i in dump():
    final[i["ref"]] = i
with open("pins.json", "w", encoding="utf-8") as f:
    json.dump(final, f, indent=1)
print("FINAL:", {k: (v["loc"], list(v["pins"])) for k, v in final.items()})
