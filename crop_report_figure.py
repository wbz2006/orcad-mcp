"""crop_report_figure.py — 从 Capture 打印的原理图 PDF 生成报告用裁剪图(300dpi PNG)。

电路范围 = 饱和色描线(非黑/灰)的并集——图纸边框/标题栏是黑线自然排除;
再并入电路周边 30pt 内的文本(VOFF 等属性块)与图注行(x<460 的同带文字);
最后白覆盖"电路底缘以下、图注右侧"的右下矩形(标题栏所在,它与电路横向重叠)。

用法: python crop_report_figure.py 图.pdf 输出.png [图注右界=460]
"""
import sys
import pymupdf
from PIL import Image

pdf, out = sys.argv[1], sys.argv[2]
cap_right_limit = float(sys.argv[3]) if len(sys.argv) > 3 else 460.0
doc = pymupdf.open(pdf)
p = doc[0]
W, H = p.rect.width, p.rect.height
xs, ys, xe, ye = 1e9, 1e9, -1e9, -1e9
for d in p.get_drawings():
    col = d.get('color') or (0, 0, 0)
    if max(col) - min(col) < 0.2:   # 黑/灰(边框/标题栏)跳过
        continue
    r = d['rect']
    xs, ys = min(xs, r.x0), min(ys, r.y0)
    xe, ye = max(xe, r.x1), max(ye, r.y1)
S = pymupdf.Rect(xs, ys, xe, ye)
box = pymupdf.Rect(S)
words = p.get_text('words')
for w in words:
    r = pymupdf.Rect(w[:4])
    if r.intersects(pymupdf.Rect(S.x0-30, S.y0-30, S.x1+30, S.y1+30)):
        box |= r                     # 属性文本(VOFF/VAMPL 等)
band, cap_right = None, 0.0
for w in words:
    if '图4.' in w[4]:
        band = w[1]
if band is not None:
    for w in words:
        r = pymupdf.Rect(w[:4])
        if abs(r.y0 - band) < 3 and r.x0 < cap_right_limit:
            box |= r; cap_right = max(cap_right, r.x1)
m = 14
clip = pymupdf.Rect(max(0, box.x0-m), max(0, box.y0-m), min(W, box.x1+m), min(H, box.y1+m))
pix = p.get_pixmap(dpi=300, clip=clip)
pix.save(out)
im = Image.open(out); sc = 300/72
wx0 = max(0, min(int(((cap_right or S.x1) + 10 - clip.x0)*sc), im.width))
wy0 = max(0, min(int((S.y1 + 5 - clip.y0)*sc), im.height))
if wx0 < im.width and wy0 < im.height:
    im.paste((255, 255, 255), (wx0, wy0, im.width, im.height))
    im.save(out)
print(f'{out}: {im.width}x{im.height}px')
