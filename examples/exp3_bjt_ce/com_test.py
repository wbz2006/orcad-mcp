import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32com.client as w
try:
    app = w.GetActiveObject("Capture.Application")
    print("attached:", app)
except Exception as e:
    print("attach fail:", e)
    raise SystemExit
try:
    doc = app.ActiveDocument
    print("doc:", doc)
except Exception as e:
    print("no active doc:", e)
