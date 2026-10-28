# -*- coding: utf-8 -*-
"""根据最新 PSpice 输出(电容值已改为 10uF/47uF)重新生成 图3.2/图3.4/表3.1。
注意:不重新生成 图3.1(图3.1 为 Capture 页面真实截图)。"""
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = r"D:\Users\Download\exp3_BJT_CE"
STUDENT = "班级: 信255   姓名: 王保哲"

# ---------------------------------------------------------------- 图3.4 数据
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
print(f"rows={len(rows)} Vs={Vs_amp:.2f} Vi={Vi_amp:.2f} Vo={Vo_amp:.2f} Av={Av:.1f}")

# ---------------------------------------------------------------- 图3.2 文本
bias = open(OUT + r"\bias.out", encoding="latin-1").read()
lines = bias.splitlines()
stamp = next(ln for ln in lines if ln.startswith("**** 10/"))
profile = next(ln for ln in lines if ln.startswith(" ** Profile"))
start = next(i for i, ln in enumerate(lines) if "SMALL SIGNAL BIAS SOLUTION" in ln)
end = next(i for i, ln in enumerate(lines) if ln.strip().startswith("FT/FT2"))
body = [ln.rstrip() for ln in lines[start:end + 1] if ln.strip()]
with open(OUT + r"\图3.2_静态工作点分析结果.txt", "w", encoding="gbk", errors="ignore") as f:
    f.write("图3.2  静态工作点分析结果(Bias Point)\n信255  王保哲\n" + "=" * 76 + "\n")
    f.write(stamp + "\n" + profile + "\n" + "=" * 76 + "\n")
    f.write("\n".join(body) + "\n")
print("图3.2 written")

# ---------------------------------------------------------------- 图3.4 波形
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
print("图3.4 written")

# ---------------------------------------------------------------- 表3.1
ic = re.search(r"IC\s+([\d.E+-]+)", bias).group(1)
vce = re.search(r"VCE\s+([\d.E+-]+)", bias).group(1)
ib = re.search(r"IB\s+([\d.E+-]+)", bias).group(1)
vbe = re.search(r"VBE\s+([\d.E+-]+)", bias).group(1)
with open(OUT + r"\表3.1_静态工作点与放大倍数数据.txt", "w", encoding="gbk", errors="ignore") as f:
    f.write("表3.1 静态工作点对放大电路参数影响(IcQ≈2.5mA 档, 仿真实测值)\n" + STUDENT + "\n" + "-" * 60 + "\n")
    f.write(f"静态工作点:  IB={float(ib)*1e6:.1f}uA   IC={float(ic)*1e3:.2f}mA   "
            f"VCE={float(vce):.2f}V   (VBE={float(vbe):.3f}V)\n")
    f.write(f"保持输入信号 Vs/mV = {Vs_amp:.2f} (设定 5mV)\n")
    f.write(f"测量值:  Vs={Vs_amp:.2f}mV   Vi={Vi_amp:.2f}mV   Vo={Vo_amp:.2f}mV\n")
    f.write(f"由测量计算:  Av(有负载 RL=2k) = Vo/Vi = {Av:.1f}\n")
    f.write("注: Ri、Ro 与空载 Av' 需按实验指导书用二次测量法补测。\n")
print("表3.1 written")
