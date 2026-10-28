# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image, ImageDraw, ImageFont
im = Image.open(r"D:\Main_FIles\free-deng\orcad-mcp\screen48.png").convert("RGB")
box = (545, 468, 1945, 1145)
fig = im.crop(box)
d = ImageDraw.Draw(fig)
ox, oy = box[0], box[1]
d.rectangle([1405-ox, 1132-oy, fig.width, fig.height], fill="white")
d.rectangle([620-ox, 1111-oy, 870-ox, 1134-oy], fill="white")
f17 = ImageFont.truetype(r"C:\Windows\Fonts\simsun.ttc", 17)
d.text((562-ox, 482-oy), "班级:信255    姓名:王保哲", fill=(30,30,30), font=f17)
d.text((1404-ox, 1114-oy), "0", fill=(0,0,150), font=f17)
fig.save(r"D:\Main_FIles\free-deng\orcad-mcp\fig31_new.png")
print(fig.size)


