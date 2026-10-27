"""实验3连线脚本:Vs 转180° → 全部导线 → 结点 → 地/别名/文本 → 验证."""
import sys, os, time, json
sys.path.insert(0, ".")
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
from build_exp3 import parse_insts

dx.ensure_capture()
s = br.BRIDGE.session()

DUMP = dx.SETUP_TCL + r'''
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
'''


def pins_by_ref():
    raw = s.eval(DUMP, 120)
    res = {}
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
        res[ref] = pins
    return res


# 1) Vs 转 180° 使 + 朝上
P = pins_by_ref()
vid = None
raw = s.eval(dx.SETUP_TCL + r'''
set pg [GetActivePage]
set st [DboState]
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $null } {
        set rn "?"
        catch { set c [DboTclHelper_sMakeCString]; $pl GetReference $c; set rn [DboTclHelper_sGetConstCharPtr $c] }
        if { $rn eq "Vs" } { $pl SetRotation 2; return "rotated" }
    }
    set i [$it NextPartInst $st]
}
return "Vs not found"
''', 60)
print("Vs:", raw)
time.sleep(0.4)
P = pins_by_ref()
print("Vs pins:", P.get("Vs"))
print("Vcc pins:", P.get("Vcc"))
json.dump(P, open("pins.json", "w", encoding="utf-8"), indent=1)
