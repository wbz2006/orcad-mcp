# -*- coding: utf-8 -*-
import os, shutil
from PIL import Image
SRC = r"D:\Main_FIles\free-deng\orcad-mcp\fig31_new.png"
DST = r"D:\Users\Download\exp3_BJT_CE"
png = os.path.join(DST, "图3.1_共射极仿真电路原理图.png")
pdf = os.path.join(DST, "图3.1_共射极仿真电路原理图.pdf")
shutil.copyfile(SRC, png)
im = Image.open(SRC).convert("RGB")
im.save(pdf, "PDF", resolution=150.0)
print("png", os.path.getsize(png), "pdf", os.path.getsize(pdf), im.size)
