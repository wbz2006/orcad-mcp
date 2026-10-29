# -*- coding: utf-8 -*-
"""静态工作点图: 从 PSpice 的 .out 里截取"电路描述 + 静态工作点 + MOSFET 工作点"
两段(去掉 evalAA.lib 的整库回显), 另存 *_fig.out 后仍由 PSpice A/D 自身打印。"""
import sys, os, time
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
import orcad_quiet as Q

TRY = r"D:\Users\Download\try"
OUT = r"C:\Users\wbz\AppData\Local\Temp\opencode"
NAME = "信255_王保哲"

JOBS = [
    ("bias_nmos.out",    "fig_46.pdf",  "图4.6 静态工作点 VGS=3V VDS=5V"),
    ("amp10k_bias.out",  "fig_420.pdf", "图4.20 静态工作点 R1=10k"),
    ("amp100k_bias.out", "fig_426.pdf", "图4.26 静态工作点 R1=100k"),
]


def excerpt(src):
    lines = open(src, encoding="utf-8", errors="replace").read().splitlines()
    marks = [i for i, l in enumerate(lines)
             if ("**** INCLUDING" in l) or ("MOSFET MODEL PARAMETERS" in l)]
    cut = min(marks) if marks else len(lines)
    head = lines[:min(4, cut)]          # 只保留时间戳横幅 + 用例名
    while head and (head[-1].strip() == ""):
        head.pop()
    b = next(i for i, l in enumerate(lines) if "SMALL SIGNAL BIAS SOLUTION" in l)
    start = max(i for i in range(b) if lines[i].startswith("**** "))
    e = next(i for i, l in enumerate(lines) if "JOB CONCLUDED" in l)
    body = lines[start:e + 1]
    # 去掉 body 里可能残留的模型参数表
    out, skip = [], False
    for l in body:
        if "MOSFET MODEL PARAMETERS" in l:
            skip = True
            while out and out[-1].startswith("**** "):
                out.pop()
            continue
        if skip:
            if l.startswith("**** "):
                skip = False
            else:
                continue
        out.append(l)
    return "\n".join(head + [""] + out) + "\n"


if __name__ == "__main__":
    only = sys.argv[1:] or None
    h = Q.probe_frame()
    assert h, "PSpice A/D 未启动"
    for out, pdf, cap in JOBS:
        if only and out not in only:
            continue
        src = os.path.join(TRY, out)
        fig = os.path.join(TRY, out.replace(".out", "_fig.out"))
        open(fig, "w", encoding="utf-8").write(excerpt(src))
        dst = os.path.join(OUT, pdf)
        Q.quiet_close_all_children(h)
        Q.quiet_open_dat(h, fig)
        ok = Q.quiet_print(h, dst, os.path.basename(fig))
        print(out, "print", ok, "pages", end=" ")
        import pymupdf
        d = pymupdf.open(dst); print(d.page_count); d.close()
        if ok:
            Q.annotate_pdf(dst, cap, NAME)
            print("  annotated", Q.pdf_has(dst, cap, NAME))
