# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp4_common as C

C.ensure_capture()
tcl = open(sys.argv[1], encoding="utf-8-sig").read()
print(C.cap(C.SETUP_TCL + tcl, float(sys.argv[2]) if len(sys.argv) > 2 else 120))
