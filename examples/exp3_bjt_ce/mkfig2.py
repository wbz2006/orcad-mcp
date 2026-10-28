# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image, ImageDraw, ImageFont
im = Image.open(r"D:\Main_FIles\free-deng\orcad-mcp\screen48.png").convert("RGB")
box = (566, 452, 1940, 1152)
fig = im.crop(box)
d = ImageDraw.Draw(fig)
ox, oy = box[0], box[1]
d.rectangle([1398-ox, 1122-oy, fig.width, fig.height], fill="white")
d.rectangle([630-ox, 1098-oy, 810-ox, 1130-oy], fill="white")
f17 = ImageFont.truetype(r"C:\Windows\Fonts\simsun.ttc", 17)
d.text((582-ox, 466-oy), "班级:信255    姓名:王保哲", fill=(30,30,30), font=f17)
fig.save(r"D:\Main_FIles\free-deng\orcad-mcp\fig31_new.png")
print(fig.size)
