# -*- coding: utf-8 -*-
import ctypes, os
out = ["user=%s" % os.environ.get("USERNAME")]
u = ctypes.windll.user32
out.append("SetCursorPos=%d" % u.SetCursorPos(700, 400))
class P(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
p = P(); u.GetCursorPos(ctypes.byref(p))
out.append("cursor=%d,%d" % (p.x, p.y))
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "elev_test.txt"), "w").write("\n".join(out))
