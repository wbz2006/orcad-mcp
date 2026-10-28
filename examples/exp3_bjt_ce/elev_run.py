# -*- coding: utf-8 -*-
"""Run a python script elevated, capturing its stdout/stderr into <script>.elev.log"""
import sys, os, runpy, io, traceback

here = os.path.dirname(os.path.abspath(__file__))
script = sys.argv[1]
log = os.path.join(here, os.path.splitext(os.path.basename(script))[0] + ".elev.log")
args = sys.argv[2:]
sys.argv = [script] + args
buf = io.StringIO()
old_out, old_err = sys.stdout, sys.stderr
sys.stdout = buf
sys.stderr = buf
code = 0
try:
    runpy.run_path(os.path.join(here, script), run_name="__main__")
except SystemExit as e:
    code = e.code if isinstance(e.code, int) else 0
except Exception:
    traceback.print_exc()
    code = 1
finally:
    sys.stdout, sys.stderr = old_out, old_err
    open(log, "w", encoding="utf-8").write(buf.getvalue())
sys.exit(code)
