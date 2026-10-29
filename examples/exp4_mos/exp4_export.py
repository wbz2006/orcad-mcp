# -*- coding: utf-8 -*-
"""exp4 Probe 批量导出(避开 PowerShell 对括号参数的解析问题)。"""
import sys, os
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
import orcad_quiet as Q

TRY = r"D:\Users\Download\try"
OUT = r"C:\Users\wbz\AppData\Local\Temp\opencode"
NAME = "信255_王保哲"

JOBS = [
    ("amp10k_dc",   "fig_418.pdf",  ["V(1)", "V(2)"],            "图4.18 共源放大器输入输出特性曲线 R1=10k", False),
    ("amp10k_ac",   "fig_423.pdf",  ["dB(V(2))", "Vp(2)"],       "图4.23 小信号相频(上)/幅频(下)特性 R1=10k", True),
    ("amp100k_dc",  "fig_425.pdf",  ["V(1)", "V(2)"],            "图4.25 共源放大器输入输出特性曲线 R1=100k", False),
    ("amp100k_ac",  "fig_428.pdf",  ["dB(V(2))", "Vp(2)"],       "图4.28 小信号相频(上)/幅频(下)特性 R1=100k", True),
]

if __name__ == "__main__":
    only = sys.argv[1:] or None
    for dat, pdf, traces, cap, two in JOBS:
        if only and dat not in only:
            continue
        src = os.path.join(TRY, dat + ".dat")
        dst = os.path.join(OUT, pdf)
        r = Q.quiet_export(src, dst, traces, caption=cap, name=NAME, two_frame=two)
        print(dat, "->", r)
