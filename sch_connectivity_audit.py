"""sch_connectivity_audit.py — 原理图引脚级连通性审计(不靠人眼)。

对指定页做:
  1. dump 全部元件引脚热点(GetOffsetHotSpot)、导线端点(GetStartPoint/GetEndPoint)、
     结点(NewJunctionsIter);
  2. 并查集: 同坐标端点-端点/端点-引脚合并;导线端点落在另一根导线**中间**只有
     存在结点对象才算连通(否则记 T-TOUCH 警告);十字交叉不算连通(记 CROSS 警告);
  3. 报告每个"没有任何导线相连"的悬空引脚(按宿主元件位置标注)。

用法: python sch_connectivity_audit.py PAGE1 PAGE2 ...   (缺省 PAGE2~5)
"""
import sys
import time

sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
import bridge as br
import capture_guard as cg
import win32gui
import win32con
import win32api
import print_export as pe

HEADER = r'''
if { [catch { set _s $::DboSession_s_pDboSession }] } { return "no Dbo session" }
DboSession -this $_s
set _st [DboState]
set _null NULL
'''

DUMP = HEADER + r'''
set pg [GetActivePage]
set out {}
# 元件+引脚+包围盒
set it [$pg NewPartInstsIter $_st]
set i [$it NextPartInst $_st]
while { $i != $_null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $_null } {
        set lc [$pl GetLocation $_st]
        set lx [DboTclHelper_sGetCPointX $lc]
        set ly [DboTclHelper_sGetCPointY $lc]
        set pit [$pl NewPinsIter $_st]
        set pin [$pit NextPin $_st]
        set pins {}
        while { $pin != $_null } {
            set sp [$pin GetOffsetHotSpot $_st]
            lappend pins "[DboTclHelper_sGetCPointX $sp],[DboTclHelper_sGetCPointY $sp]"
            set pin [$pit NextPin $_st]
        }
        catch { delete_DboPartInstPinsIter $pit }
        set bb "0,0,0,0"
        if { ![catch {
            set box [$pl GetBoundingBox]
            set tl [DboTclHelper_sGetCRectTopLeft $box]
            set br [DboTclHelper_sGetCRectBottomRight $box]
            set bb "[DboTclHelper_sGetCPointX $tl],[DboTclHelper_sGetCPointY $tl],[DboTclHelper_sGetCPointX $br],[DboTclHelper_sGetCPointY $br]"
        }] } { }
        lappend out "PART|$lx,$ly|[join $pins ,]|$bb"
    }
    set i [$it NextPartInst $_st]
}
delete_DboPagePartInstsIter $it
# 导线
set wit [$pg NewWiresIter $_st]
set w [$wit NextWire $_st]
while { $w != $_null } {
    set sp [$w GetStartPoint $_st]
    set ep [$w GetEndPoint $_st]
    lappend out "WIRE|[DboTclHelper_sGetCPointX $sp],[DboTclHelper_sGetCPointY $sp]|[DboTclHelper_sGetCPointX $ep],[DboTclHelper_sGetCPointY $ep]"
    set w [$wit NextWire $_st]
}
catch { delete_DboPageWiresIter $wit }
# 结点
if { ![catch { set jit [$pg NewJunctionsIter $_st] }] } {
    set j [$jit NextJunction $_st]
    while { $j != $_null } {
        lappend out "JCT|[DboTclHelper_sGetCPointX $j],[DboTclHelper_sGetCPointY $j]"
        set j [$jit NextJunction $_st]
    }
    catch { delete_DboWireJunctionsIter $jit }
}
join $out "\n"
'''


def activate(s, pg):
    cap = []
    win32gui.EnumWindows(lambda h, _: cap.append(h)
                         if win32gui.IsWindowVisible(h) and "OrCAD Capture" in win32gui.GetWindowText(h) else True, None)
    pe.set_fore(cap[0])
    s.eval(f'SelectPMItem {{{pg}}}', timeout=30)
    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0); time.sleep(0.05)
    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(2.2)


def parse(raw):
    parts, wires, jcts = [], [], []
    for line in raw.splitlines():
        f = line.strip().split("|")
        if f[0] == "PART":
            loc = tuple(map(int, f[1].split(",")))
            nums = [int(x) for x in f[2].split(",") if x]  # 引脚被", "拍平: 两两成对还原
            pins = [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
            bb = tuple(map(int, f[3].split(","))) if len(f) > 3 and f[3] else (0, 0, 0, 0)
            parts.append((loc, pins, bb))
        elif f[0] == "WIRE":
            wires.append((tuple(map(int, f[1].split(","))), tuple(map(int, f[2].split(",")))))
        elif f[0] == "JCT":
            jcts.append(tuple(map(int, f[1].split(","))))
    return parts, wires, jcts


def on_seg(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    if ax == bx:
        return px == ax and min(ay, by) < py < max(ay, by)
    if ay == by:
        return py == ay and min(ax, bx) < px < max(ax, bx)
    return False


def audit_page(name, raw):
    parts, wires, jcts = parse(raw)
    jset = set(jcts)
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    ends = []
    for a, b in wires:
        ends.append(a)
        ends.append(b)
        union(a, b)
    ep_map = {}
    for e in ends:
        ep_map.setdefault(e, e)
    for entry in parts:
        for p in entry[1]:
            parent.setdefault(p, p)
            if p in ep_map:  # 引脚落在导线端点上 → 并入该导线组
                union(p, ep_map[p])

    warn_t, warn_cross = [], []
    for a, b in wires:
        for e in set(ends):
            if e in (a, b):
                continue
            if on_seg(e, a, b):
                if e in jset:
                    union(e, a)
                else:
                    warn_t.append((e, (a, b)))
    # 十字交叉(垂直相交且都不是端点):不算连通,列出防误读
    for i, (a1, b1) in enumerate(wires):
        for a2, b2 in wires[i + 1:]:
            if a1[0] == b1[0] and a2[1] == b2[1]:
                x, y = a1[0], a2[1]
                if min(a1[1], b1[1]) < y < max(a1[1], b1[1]) and min(a2[0], b2[0]) < x < max(a2[0], b2[0]):
                    warn_cross.append((x, y))
            elif a1[1] == b1[1] and a2[0] == b2[0]:
                x, y = a2[0], a1[1]
                if min(a2[1], b2[1]) < y < max(a2[1], b2[1]) and min(a1[0], b1[0]) < x < max(a1[0], b1[0]):
                    warn_cross.append((x, y))

    floating = []
    for entry in parts:
        loc, pins = entry[0], entry[1]
        for p in pins:
            # 悬空 = 不在任何导线端点上,也没通过结点/T并入任何组(组内只有自己)
            if p not in ep_map and find(p) == p:
                floating.append((loc, p))

    # 导线穿符号检查(两种缺陷模式: 端点扎进符号体内且不是引脚;导线整体横穿符号。
    # 判据用"引脚包络核"(pins bbox ± 5),不用 GetBoundingBox——后者含显示属性文本,
    # 会把贴着标签的导线误报。引脚引入段是正常画法,不报)
    through = []
    for loc, pins, bb in parts:
        if not pins:
            continue
        pxs = [p[0] for p in pins]
        pys = [p[1] for p in pins]
        m = 5
        x1, y1, x2, y2 = min(pxs) - m, min(pys) - m, max(pxs) + m, max(pys) + m
        pinset = set(pins)
        for a, b in wires:
            (ax, ay), (bx, by) = a, b
            lox, hix = min(ax, bx), max(ax, bx)
            loy, hiy = min(ay, by), max(ay, by)
            hit = False
            for e in (a, b):
                if e not in pinset and x1 <= e[0] <= x2 and y1 <= e[1] <= y2:
                    hit = True  # 端点扎进符号体内且不是引脚
            if not hit and ax == bx and loy < y1 and hiy > y2 and x1 <= ax <= x2:
                hit = True  # 竖线整体横穿
            if not hit and ay == by and lox < x1 and hix > x2 and y1 <= ay <= y2:
                hit = True  # 横线整体横穿
            if hit:
                through.append((loc, (a, b)))

    groups = {}
    for e in set(ends):
        groups.setdefault(find(e), []).append(e)
    print(f"=== {name}: 元件{len(parts)} 导线{len(wires)} 结点{len(jcts)} "
          f"连通组{len(groups)} 悬空引脚{len(floating)} 穿符号{len(through)}")
    for loc, p in floating:
        print(f"  悬空: 元件@{loc} 引脚@{p}")
    for loc, seg in through:
        print(f"  穿符号: 元件@{loc} 的线段{seg} 扎入或横穿符号体")
    for e, seg in warn_t:
        print(f"  T-TOUCH无结点: 端点{e} 落在{seg}中间(电气未连通!)")
    for c in warn_cross:
        print(f"  交叉(无结点,不连通,仅提示): {c}")
    return not floating and not warn_t and not through


if __name__ == "__main__":
    b = br.Bridge(int(__import__("os").environ.get("ORCAD_MCP_PORT", "5177")))
    b.ensure()
    s = None
    for _ in range(15):
        try:
            s = b.session(); break
        except Exception:
            time.sleep(1)
    pages = sys.argv[1:] or ["PAGE2", "PAGE3", "PAGE4", "PAGE5"]
    all_ok = True
    for pg in pages:
        activate(s, pg)
        raw = cg.eval_safe(s, DUMP, timeout=25)
        all_ok &= audit_page(pg, raw)
    print("审计结论:", "全部通过" if all_ok else "存在问题,见上")
