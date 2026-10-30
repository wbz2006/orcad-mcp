"""relayout_fig415.py — 实战示例:按手册图4.15 实测比例,全页重排共源放大器。

(实验4 第四轮,2026-10-29。本脚本是把"量手册 → 列坐标表 → 删/移/布线 → 校验"
固化的可复用模板:换电路/换手册图时,只需重测比例、替换 DEL/WIRE/MOVES 三张表。)

【第一步:量手册】以一个已知尺寸的元件为标尺(本例 M2 本体高 = 40 单位,即 0.01inch
单位下符号引脚跨度),在手册插图上量出所有间距,乘 (标尺实际单位/标尺像素):

    手册图4.15 实测(px,图宽 731)     × 0.8 (40单位/50px)  → 设计单位
    ─────────────────────────────────────────────────────────────────
    顶轨距 R1 顶                      45px  → 36  (取 28,受符号引脚跨度 40 约束)
    R1 底 → M2 漏                     80px  → 64
    M2 源 → 底轨                      145px → 116
    V1 与 R1 同高带(V1− 距 R1 底)    20px  → 16
    顶轨角 → V1+                      55px  → 44
    V1− → 底轨                        255px → 204
    V2 竖引线(底轨→栅线高)          110px → 88
    V2 矮脚(本体→底轨)               10px  → 8
    V2 列距 M2 列                     273px → 218
    V1 列距 M2 列                     242px → 194

【第二步:列坐标表】锚定一个元件不动(本例 M2 (600,380)),其余全部由间距推出。
【第三步:按页执行】删旧线(端点匹配+原生 Delete)→ 移件/GND(SetLocation **不带
status**)→ PlaceWire 布新线(英寸、y 向下;允许自动分段,以最终 dump 为准)→
仅在 T 型接入处 PlaceJunction → save_verified。
【第四步:机器闸门】sch_connectivity_audit.py(悬空/横穿/T触)→ 打印 PDF →
crop_report_figure.py 出报告特写图。

注意:
- 基极(B)按手册与源极**同一条线**入地:符号旁短接 (630,430)-(620,430) +
  PlaceJunction (620,430),源极单线下地;不要走独立衬底回线。
- 结点放在"端点落在另一根线中间"的 T 点;≥3 线端点相接 Capture 自动画圆点,无需结点。
- 批量前跑 `capture_guard.py health`,全程 eval 用 capture_guard.eval_safe。
"""
import sys
import time

sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
import bridge as br
import capture_guard as cg
import sch_connectivity_audit as sca

DSN = r"D:\Users\Download\try\EXP4.DSN"

# ── 删:旧布局全部导线(端点对,顺序无关) ────────────────────────────────
DEL = [
    (700, 120, 620, 120),   # 旧顶轨横段
    (620, 120, 620, 270),   # 旧顶轨竖段(到 R1 顶)
    (620, 310, 620, 380),   # 旧 R1→漏
    (700, 140, 700, 120),   # 旧 V1+ 竖引
    (700, 470, 700, 180),   # 旧 V1− 长落
    (270, 470, 620, 470),   # 旧底轨西段
    (620, 470, 630, 470),   # 旧底轨延伸 ×3(PlaceWire 分段产物)
    (630, 470, 650, 470),
    (650, 470, 700, 470),
    (620, 420, 620, 470),   # 旧源极下引
    (630, 430, 650, 430),   # 旧衬底回字形 ×2
    (650, 430, 650, 470),
    (270, 420, 270, 400),   # 旧 V2/V3 竖引
    (270, 460, 270, 470),   # 旧 V2/V3 矮脚
    (270, 400, 590, 400),   # 旧栅线
]

# ── 移:元件与 GND(SetLocation 不带 status)────────────────────────────
# R1  (610,280)→(610,286)  引脚变 (620,276)/(620,316)
# V1  (690,140)→(800,292)  引脚变 (810,292)/(810,332)  [VDC 引脚=loc+(10,0)/(10,40)]
# V2  (260,420)→(390,488)  引脚变 (400,488)/(400,528)  [同上]
# V3  (260,430)→(390,498)  引脚变 (400,488)/(400,528)  [VSIN 引脚=loc+(10,-10)/(10,30)]
# GND (620,470)→(620,536)  挂底轨
MOVES_PART = [
    (610, 280, 610, 286),
    (690, 140, 800, 292),
]
MOVE_V = {True: (260, 430, 390, 498),   # PAGE3/PAGE5 用 V3
          False: (260, 420, 390, 488)}  # PAGE2/PAGE4 用 V2
MOVE_GND = (620, 470, 620, 536)

# ── 布:新布局全部导线(英寸;跨越其它线端点会被自动分段,属正常) ─────────
WIRE = [
    (6.20, 2.48, 6.20, 2.76),   # 顶轨竖段:轨→R1 顶
    (6.20, 2.48, 8.10, 2.48),   # 顶轨横段:R1 列→V1 列
    (8.10, 2.48, 8.10, 2.92),   # V1+ 下引 44
    (8.10, 3.32, 8.10, 5.36),   # V1− 长落 204
    (4.00, 5.36, 6.20, 5.36),   # 底轨西段:V2 列→源极结点
    (6.20, 5.36, 8.10, 5.36),   # 底轨东段:源极结点→V1 列
    (6.20, 4.20, 6.20, 5.36),   # 源极下引 116(会被基极并接点分段)
    (6.30, 4.30, 6.20, 4.30),   # 基极-源极并接短线 10
    (4.00, 4.00, 4.00, 4.88),   # V2/V3 竖引 88
    (4.00, 4.00, 5.90, 4.00),   # 栅线
    (4.00, 5.28, 4.00, 5.36),   # V2/V3 矮脚 8
    (6.20, 3.16, 6.20, 3.80),   # R1→漏 64
]
JUNCTIONS = [(6.20, 4.30)]      # 仅基极并接 T 点需要;其余全是端点相接

PAGES = {"PAGE2": False, "PAGE3": True, "PAGE4": False, "PAGE5": True}  # True=V3

HEADER = r'''
if { [catch { set _s $::DboSession_s_pDboSession }] } { return "no Dbo session" }
DboSession -this $_s
set _st [DboState]
set _null NULL
'''

FIND_DEL = HEADER + r'''
set pg [GetActivePage]
set wit [$pg NewWiresIter $_st]
set w [$wit NextWire $_st]
set found 0
while { $w != $_null && $found == 0 } {
    set sp [$w GetStartPoint $_st]
    set ep [$w GetEndPoint $_st]
    set sx [DboTclHelper_sGetCPointX $sp]; set sy [DboTclHelper_sGetCPointY $sp]
    set ex [DboTclHelper_sGetCPointX $ep]; set ey [DboTclHelper_sGetCPointY $ep]
    if { ($sx==P1X && $sy==P1Y && $ex==P2X && $ey==P2Y) ||
         ($sx==P2X && $sy==P2Y && $ex==P1X && $ey==P1Y) } {
        set found [$w GetId $_st]
    }
    set w [$wit NextWire $_st]
}
catch { delete_DboPageWiresIter $wit }
if { $found == 0 } { return "nomatch" } else { return $found }
'''

MOVE_PART = HEADER + r'''
set pg [GetActivePage]
set it [$pg NewPartInstsIter $_st]
set i [$it NextPartInst $_st]
set moved 0
while { $i != $_null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $_null } {
        set lc [$pl GetLocation $_st]
        if { [DboTclHelper_sGetCPointX $lc]==OX && [DboTclHelper_sGetCPointY $lc]==OY } {
            $pl SetLocation [DboTclHelper_sMakeCPoint NX NY]
            set moved 1
        }
    }
    set i [$it NextPartInst $_st]
}
catch { delete_DboPagePartInstsIter $it }
return "moved=$moved"
'''

MOVE_GLOB = HEADER + r'''
set pg [GetActivePage]
set git [$pg NewGlobalsIter $_st]
set g [$git NextGlobal $_st]
set moved 0
while { $g != $_null } {
    set lc [$g GetLocation $_st]
    if { [DboTclHelper_sGetCPointX $lc]==OX && [DboTclHelper_sGetCPointY $lc]==OY } {
        $g SetLocation [DboTclHelper_sMakeCPoint NX NY]
        set moved 1
    }
    set g [$git NextGlobal $_st]
}
catch { delete_DboPageGlobalsIter $git }
return "moved=$moved"
'''


def main():
    b = br.Bridge(int(__import__("os").environ.get("ORCAD_MCP_PORT", "5177")))
    b.ensure()
    s = None
    for _ in range(20):
        try:
            s = b.session()
            if s.ping(timeout=3):
                break
        except Exception:
            pass
        s = None
        time.sleep(1)
    assert s, "no agent — 先跑 capture_guard.py health 排查"

    for pg, is_v3 in PAGES.items():
        sca.activate(s, pg)
        for (x1, y1, x2, y2) in DEL:
            tcl = (FIND_DEL.replace("P1X", str(x1)).replace("P1Y", str(y1))
                   .replace("P2X", str(x2)).replace("P2Y", str(y2)))
            r = cg.eval_safe(s, tcl, timeout=25)
            if r == "nomatch":
                print(pg, "del nomatch", (x1, y1, x2, y2))
                continue
            cg.eval_safe(s, f"SelectObjectById {r}", timeout=20)
            cg.eval_safe(s, 'Menu "Edit::Delete"', timeout=25)
        for (ox, oy, nx, ny) in MOVES_PART:
            tcl = (MOVE_PART.replace("OX", str(ox)).replace("OY", str(oy))
                   .replace("NX", str(nx)).replace("NY", str(ny)))
            cg.eval_safe(s, tcl, timeout=25)
        ox, oy, nx, ny = MOVE_V[is_v3]
        tcl = (MOVE_PART.replace("OX", str(ox)).replace("OY", str(oy))
               .replace("NX", str(nx)).replace("NY", str(ny)))
        cg.eval_safe(s, tcl, timeout=25)
        tcl = (MOVE_GLOB.replace("OX", str(MOVE_GND[0])).replace("OY", str(MOVE_GND[1]))
               .replace("NX", str(MOVE_GND[2])).replace("NY", str(MOVE_GND[3])))
        cg.eval_safe(s, tcl, timeout=25)
        for (x1, y1, x2, y2) in WIRE:
            cg.eval_safe(s, "PlaceWire %.2f %.2f %.2f %.2f" % (x1, y1, x2, y2), timeout=30)
            time.sleep(0.35)
        for (x, y) in JUNCTIONS:
            cg.eval_safe(s, "PlaceJunction %.2f %.2f" % (x, y), timeout=25)
        time.sleep(0.3)
        st = cg.save_verified(s, DSN)
        print(pg, "save:", st)
    print("重排完成。下一步:python sch_connectivity_audit.py → 打印 → crop_report_figure.py")


if __name__ == "__main__":
    main()
