"""实验3交付物生成 v2(镜像布局):图3.1/3.2/3.4 + 表3.1."""
import json
import math
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

OUT = r"D:\Users\Download\exp3_BJT_CE"
STUDENT = "班级:________   姓名:________"

# ------------------------------------------------------------- 图3.2 文字
bias = open(OUT + r"\bias.out", encoding="latin-1").read()
lines = bias.splitlines()
keep_idx = next(i for i, ln in enumerate(lines) if "*** BIPOLAR" in ln)
head = [ln for ln in lines[:keep_idx]
        if ("Profile" in ln or "Pspice" in ln.lower() or "OPERATING POINT" in ln
            or ln.startswith("*") or "TEMPERATURE" in ln)]
with open(OUT + r"\图3.2_静态工作点分析结果.txt", "w", encoding="gbk", errors="ignore") as f:
    f.write("图3.2 静态工作点分析结果(Bias Point)\n" + STUDENT + "\n" + "=" * 64 + "\n")
    for ln in head:
        if ln.strip():
            f.write(ln.rstrip() + "\n")
    f.write("\n".join(lines[keep_idx:keep_idx + 15]) + "\n")
print("图3.2 written")

# ------------------------------------------------------------- 波形解析
tran = open(OUT + r"\tran.out", encoding="latin-1").read()
rows, started = [], False
for ln in tran.splitlines():
    if "TIME" in ln and "V(Vs)" in ln:
        started = True
        continue
    if started:
        m = re.match(r"\s*([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+)\s+([\d.E+-]+)\s*$", ln)
        if m:
            rows.append([float(x) for x in m.groups()])
        elif rows:
            break
t = [r[0] * 1e3 for r in rows]
vs = [r[1] * 1e3 for r in rows]
vi = [r[2] * 1e3 for r in rows]
vo = [r[3] * 1e3 for r in rows]
amp = lambda xs: (max(xs) - min(xs)) / 2
Vs_amp, Vi_amp, Vo_amp = amp(vs), amp(vi), amp(vo)
Av = Vo_amp / Vi_amp
print(f"rows={len(rows)} Vm(Vi)={Vi_amp:.2f}mV Vm(Vo)={Vo_amp:.2f}mV Av={Av:.1f}")

# ------------------------------------------------------------- 图3.4 波形 PDF
fig, axs = plt.subplots(3, 1, figsize=(9, 7), sharex=True)
for ax, ys, label, color in (
        (axs[0], vs, "V(Vs)  5mV/1kHz 输入信号源", "green"),
        (axs[1], vi, "V(Vi)  经 Rs 后的净输入", "blue"),
        (axs[2], vo, "V(Vo)  输出电压(RL=2k)", "red")):
    ax.plot(t, ys, color=color, lw=1.1)
    ax.set_ylabel("电压 (mV)")
    ax.grid(True, ls=":", alpha=0.6)
    ax.set_title(label, fontsize=10, loc="left")
axs[2].set_xlabel("时间 (ms)")
axs[2].text(0.99, -0.5, STUDENT, transform=axs[2].transAxes, ha="right", fontsize=11)
fig.suptitle("图3.4  Ic=2.5mA时的 Vi、VS、Vo 波形(Transient 0~5ms)", fontsize=13)
fig.tight_layout(rect=(0, 0.02, 1, 0.96))
fig.savefig(OUT + r"\图3.4_Ic2.5mA_Vi_VS_Vo波形.pdf")
plt.close(fig)

# ------------------------------------------------------------- 表3.1
with open(OUT + r"\表3.1_静态工作点与放大倍数数据.txt", "w", encoding="gbk", errors="ignore") as f:
    f.write("表3.1 静态工作点对放大电路参数影响(IcQ≈2.5mA 档, 仿真实测值)\n" + STUDENT + "\n" + "-" * 60 + "\n")
    f.write("静态工作点:  IB=45.6uA   IC=2.51mA   VCE=4.44V   (VBE=0.689V)\n")
    f.write(f"保持输入信号 Vs/mV = {Vs_amp:.2f} (设定 5mV)\n")
    f.write(f"测量值:  Vs={Vs_amp:.2f}mV   Vi={Vi_amp:.2f}mV   Vo={Vo_amp:.2f}mV\n")
    f.write(f"由测量计算:  Av(有负载 RL=2k) = Vo/Vi = {Av:.1f}\n")
    f.write("注: Ri、Ro 与空载 Av' 需按实验指导书用二次测量法补测。\n")
print("表3.1 written")

# ------------------------------------------------------------- 图3.1 原理图
PINS = json.load(open(r"D:\Main_FIles\free-deng\orcad-mcp\pins.json", encoding="utf-8"))
VALUES = {"Rs": "1k", "C1": "10u", "Rb1": "57k", "Rc": "2k", "Rb2": "30k",
          "Re": "1k", "Ce": "47u", "C2": "10u", "RL": "2k"}


def rtop_bottom(name):
    ps = PINS[name]
    top = ps["1"] if ps["1"][1] < ps["2"][1] else ps["2"]
    bot = ps["2"] if ps["1"][1] < ps["2"][1] else ps["1"]
    return top, bot


Rb1t, Rb1b = rtop_bottom("Rb1")
Rb2t, Rb2b = rtop_bottom("Rb2")
Rct, Rcb = rtop_bottom("Rc")
Ret, Reb = rtop_bottom("Re")
Cet, Ceb = rtop_bottom("Ce")
RLt, RLb = rtop_bottom("RL")
c12 = (PINS["C1"]["2"][0] + 0.1, PINS["C1"]["2"][1])
baserail_y = PINS["Q1"]["b"][1]
col_y = 5.4
emit_y = PINS["Q1"]["e"][1] + 0.2
rail_y = 3.6
vo_x = PINS["C2"]["2"][0] + 1.7

WIRES = [
    (PINS["Vs"]["+"], (1.1, PINS["Vs"]["+"][1] - 0.3)),
    ((1.1, PINS["Vs"]["+"][1] - 0.3), (2.0, PINS["Vs"]["+"][1] - 0.3)),
    ((2.0, PINS["Vs"]["+"][1] - 0.3), (2.0, PINS["Rs"]["1"][1])),
    ((2.0, PINS["Rs"]["1"][1]), PINS["Rs"]["1"]),
    (PINS["Rs"]["2"], PINS["C1"]["1"]),
    (PINS["C1"]["2"], c12), (c12, (c12[0], baserail_y)),
    ((c12[0], baserail_y), PINS["Q1"]["b"]),
    (Rb1t, (Rb1t[0], rail_y)), (Rb1b, (Rb1b[0], baserail_y)),
    (Rb2t, (Rb2t[0], baserail_y)),
    ((Rb1t[0], rail_y), (8.6, rail_y)),
    (Rct, (Rct[0], rail_y)),
    ((8.6, rail_y), PINS["Vcc"]["+"]),
    (Rcb, (Rcb[0], col_y)), ((5.5, col_y), (7.2, col_y)),
    ((5.5, col_y), PINS["Q1"]["c"]), ((7.2, col_y), PINS["C2"]["1"]),
    (PINS["Q1"]["e"], (PINS["Q1"]["e"][0], emit_y)),
    ((5.5, emit_y), (PINS["Ce"]["1"][0], emit_y)),
    (Ret, (Ret[0], emit_y)), (Cet, (Cet[0], emit_y)),
    (PINS["C2"]["2"], (vo_x, PINS["C2"]["2"][1])),
    ((vo_x, PINS["C2"]["2"][1]), RLt),
]
JUNCTIONS = [(Rb1b[0], baserail_y), (Rb1t[0], rail_y), (Rct[0], rail_y),
             (Rcb[0], col_y), (Ret[0], emit_y)]
GROUNDS = [PINS["Vs"]["-"], Rb2b, Reb, Ceb, RLb, PINS["Vcc"]["-"]]


def draw_r(ax, p1, p2):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    lead, body = 0.06, L - 0.12
    a = (p1[0] + ux * lead, p1[1] + uy * lead)
    ax.plot([p1[0], a[0]], [p1[1], a[1]], "k-", lw=1.2)
    n = 6
    seg = body / n
    cx, cy = a
    pts = [a]
    for k in range(n):
        nx_, ny_ = a[0] + ux * seg * (k + 1), a[1] + uy * seg * (k + 1)
        mx_, my_ = a[0] + ux * seg * (k + 0.5), a[1] + uy * seg * (k + 0.5)
        off = 0.05 if k % 2 == 0 else -0.05
        pts.append((mx_ + px * off, my_ + py * off))
        pts.append((nx_, ny_))
    xs, ys = zip(*pts)
    ax.plot(xs, ys, "k-", lw=1.2)


def draw_c(ax, p1, p2):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    ux, uy = dx / (math.hypot(dx, dy)), dy / (math.hypot(dx, dy))
    c = (p1[0] + dx / 2, p1[1] + dy / 2)
    g, pl = 0.035, 0.09
    px, py = -uy, ux
    for sgn in (-1, 1):
        n = (c[0] + ux * g * sgn, c[1] + uy * g * sgn)
        ax.plot([n[0] - px * pl, n[0] + px * pl], [n[1] - py * pl, n[1] + py * pl], "k-", lw=1.4)
        if sgn < 0:
            ax.plot([p1[0], n[0]], [p1[1], n[1]], "k-", lw=1.1)
        else:
            ax.plot([n[0], p2[0]], [n[1], p2[1]], "k-", lw=1.1)


def draw_q(ax, b, c, e):
    bx = b[0] + 0.10
    ax.plot([b[0], bx], [b[1], b[1]], "k-", lw=1.2)
    ax.plot([bx, bx], [c[1] + 0.04, e[1] - 0.04], "k-", lw=1.8)
    ax.add_patch(Circle((bx + 0.09, b[1]), 0.17, fill=False, ec="k", lw=1.2))
    ax.plot([bx, c[0] - 0.02], [c[1] + 0.04 if c[1] > e[1] else e[1] - 0.04, c[1]], "k-", lw=1.1)
    ax.plot([bx, e[0] - 0.02], [e[1] - 0.04 if c[1] > e[1] else c[1] + 0.04, e[1]], "k-", lw=1.1)
    ax.annotate("", xy=(e[0] - 0.04, e[1]),
                xytext=(bx + (e[0] - bx) * 0.45, b[1] + (e[1] - b[1]) * 0.45),
                arrowprops=dict(arrowstyle="-|>", color="k", lw=1.0))


def draw_vsin(ax, plus, minus):
    cx, cy = plus[0], (plus[1] + minus[1]) / 2
    ax.add_patch(Circle((cx, cy), 0.17, fill=False, ec="k", lw=1.2))
    yy = np.linspace(cy - 0.09, cy + 0.09, 40)
    xx = cx + 0.09 * np.sin((yy - cy) / 0.09 * math.pi * 1.6)
    ax.plot(xx, yy, "k-", lw=1.0)
    ax.plot([cx, plus[0]], [plus[1], plus[1]], "k-", lw=1.1)
    ax.plot([cx, minus[0]], [minus[1], minus[1]], "k-", lw=1.1)
    ax.text(cx + 0.13, plus[1] - 0.04, "+", fontsize=12)


fig, ax = plt.subplots(figsize=(11.5, 8.2))
for p1, p2 in WIRES:
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#cc2222", lw=1.3, zorder=1)
for jx, jy in JUNCTIONS:
    ax.plot([jx], [jy], marker="o", ms=5, color="#cc2222", zorder=3)

for name in ("Rs", "Rb1", "Rc", "Rb2", "Re", "RL"):
    ps = PINS[name]
    p1, p2 = ps["1"], ps["2"]
    draw_r(ax, p1, p2)
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    horiz = abs(p2[0] - p1[0]) > abs(p2[1] - p1[1])
    if horiz:
        ax.text(mx, my - 0.16, name, fontsize=10.5, ha="center", color="darkblue")
        ax.text(mx, my + 0.17, VALUES[name], fontsize=10, ha="center")
    else:
        ax.text(mx - 0.24, my, name, fontsize=10.5, ha="center", color="darkblue")
        ax.text(mx + 0.24, my, VALUES[name], fontsize=10, ha="center")
for name in ("C1", "C2", "Ce"):
    p1, p2 = PINS[name]["1"], PINS[name]["2"]
    draw_c(ax, p1, p2)
    mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
    horiz = abs(p2[0] - p1[0]) > abs(p2[1] - p1[1])
    if horiz:
        ax.text(mx, my - 0.16, name, fontsize=10.5, ha="center", color="darkblue")
        ax.text(mx, my + 0.17, VALUES[name], fontsize=10, ha="center")
    else:
        ax.text(mx - 0.24, my, name, fontsize=10.5, ha="center", color="darkblue")
        ax.text(mx + 0.24, my, VALUES[name], fontsize=10, ha="center")
draw_q(ax, PINS["Q1"]["b"], PINS["Q1"]["c"], PINS["Q1"]["e"])
ax.text(PINS["Q1"]["b"][0] - 0.28, PINS["Q1"]["b"][1] - 0.05, "Q1", fontsize=10.5, color="darkblue")
ax.text(PINS["Q1"]["c"][0] + 0.12, PINS["Q1"]["c"][1] + 0.12, "Q2N3904", fontsize=9)
draw_vsin(ax, PINS["Vs"]["+"], PINS["Vs"]["-"])
ax.text(PINS["Vs"]["+"][0] - 0.38, PINS["Vs"]["+"][1] - 0.05, "Vs", fontsize=11, color="darkblue")
ax.text(PINS["Vs"]["+"][0] + 0.2, PINS["Vs"]["+"][1] - 0.25,
        "VOFF=0\nVAMPL=5mV\nFREQ=1kHz", fontsize=7.5)
draw_vsin(ax, PINS["Vcc"]["+"], PINS["Vcc"]["-"])
ax.text(PINS["Vcc"]["+"][0] + 0.22, PINS["Vcc"]["+"][1] - 0.05, "Vcc", fontsize=11, color="darkblue")
ax.text(PINS["Vcc"]["+"][0] - 0.9, PINS["Vcc"]["+"][1] + 0.3,
        "VOFF=12V, VAMPL=0\n(等效 12V 直流源)", fontsize=7.5)
for gx, gy in GROUNDS:
    ax.plot([gx, gx], [gy, gy + 0.07], "k-", lw=1.1)
    for k, w in ((1, 0.09), (2, 0.055), (3, 0.025)):
        ax.plot([gx - w, gx + w], [gy + 0.07 + 0.028 * k] * 2, "k-", lw=1.1)
ax.text((PINS["Rs"]["2"][0] + PINS["C1"]["1"][0]) / 2, PINS["Rs"]["2"][1] - 0.18,
        "Vi", fontsize=10.5, color="darkred")
ax.text(PINS["C2"]["2"][0] + 0.8, PINS["C2"]["2"][1] - 0.18, "Vo", fontsize=10.5, color="darkred")
ax.text(0.4, 0.45, "图3.1  共射极仿真电路原理图(β=70, Q2N3904)", fontsize=13)
ax.text(0.4, 0.8, STUDENT, fontsize=11)
ax.set_xlim(0.3, 10.0)
ax.set_ylim(0.2, 8.0)
ax.invert_yaxis()
ax.set_aspect("equal")
ax.axis("off")
fig.savefig(OUT + r"\图3.1_共射极仿真电路原理图.pdf", bbox_inches="tight")
fig.savefig(OUT + r"\图3.1_共射极仿真电路原理图.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("图3.1 written")
