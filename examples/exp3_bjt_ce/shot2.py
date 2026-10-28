# -*- coding: utf-8 -*-
import os
from PIL import ImageGrab
im = ImageGrab.grab()
p = r"D:\Main_FIles\free-deng\orcad-mcp\screen48.png"
im.save(p)
print("saved", im.size)
