# -*- coding: utf-8 -*-
"""在图4.13 转移特性上标出 VGS=5.2V / IDO=314.8mA 游标读数(图4.14)。"""
import pymupdf

SRC = r"C:\Users\wbz\AppData\Local\Temp\opencode\fig_414.pdf"
FONT = r"C:\Windows\Fonts\msyh.ttc"

doc = pymupdf.open(SRC)
page = doc[0]
W, H = page.rect.width, page.rect.height
spans = []
for b in page.get_text("dict")["blocks"]:
    for l in b.get("lines", []):
        for s in l["spans"]:
            spans.append((s["text"].strip(), s["bbox"], s["size"]))

def center(bb):
    return ((bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2)

def find(text, pred):
    for t, bb, sz in spans:
        if t == text and pred(bb):
            return center(bb)
    return None

x0 = find("1.0V", lambda bb: bb[1] > H * 0.75)
x1 = find("5.0V", lambda bb: bb[1] > H * 0.75)
y0 = find("100mA", lambda bb: bb[0] < W * 0.25)
y1 = find("300mA", lambda bb: bb[0] < W * 0.25)
print("anchors", x0, x1, y0, y1)

VGS, IDO = 5.2, 0.3148
px = x0[0] + (VGS - 1.0) / 4.0 * (x1[0] - x0[0])
py = y0[1] - (IDO - 0.100) / 0.200 * (y0[1] - y1[1])
print("point", px, py)

# 竖向虚线 + 数据点
page.draw_line(pymupdf.Point(px, y0[1]), pymupdf.Point(px, py),
               color=(0.35, 0.35, 0.35), width=0.8, dashes="[3 3] 0")
page.draw_circle(pymupdf.Point(px, py), 3.2, color=(0, 0, 0), fill=(0, 0, 0))

txt = "VGS=5.2V\nIDO=314.8mA"
box = pymupdf.Rect(px + 12, py + 18, px + 150, py + 62)
page.insert_textbox(box, txt, fontsize=11, fontname="msyh", fontfile=FONT,
                    color=(0, 0, 0), align=0)
doc.subset_fonts()
doc.save(SRC + ".tmp", garbage=4, deflate=True)
doc.close()
import os
os.replace(SRC + ".tmp", SRC)
print("ok")
