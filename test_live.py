"""Live end-to-end test: bridge + real Capture + open sample design + Dbo traversal.

会短暂启动真实 OrCAD Capture 窗口,验证后自动 Quit(不保存任何修改)。
"""

import sys
import threading
import time

sys.path.insert(0, ".")
import bridge as br  # noqa: E402
import server as sv  # noqa: E402  # 复用 server.py 里的同款 TCL 片段

SAMPLE = r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\samples\Demo\FULLADD.DSN"


def launch_com(status: list):
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    try:
        app = win32com.client.Dispatch("Capture.Application")
        status.append(app)
    except Exception as e:  # noqa: BLE001
        status.append(e)


def main() -> int:
    b = br.BRIDGE  # 与 server.py 共用单例,避免双绑定
    b.start()

    print("[test] launching Capture via COM ...")
    status: list = []
    t = threading.Thread(target=launch_com, args=(status,), daemon=True)
    t.start()
    t.join(120)
    if not status:
        print("[test] TIMEOUT: COM Dispatch did not return in 120s")
        return 1
    if isinstance(status[0], Exception):
        print(f"[test] COM Dispatch failed: {status[0]}")
        return 1

    sess = None
    deadline = time.time() + 60
    while time.time() < deadline:
        ss = b.all_sessions()
        if ss:
            sess = ss[0]
            break
        time.sleep(1)
    if sess is None:
        print("[test] TIMEOUT: agent never connected within 60s")
        return 1
    print(f"[test] agent connected: {sess.info}")

    ok = True

    def check(name, fn):
        nonlocal ok
        try:
            r = fn()
            passed = True
        except Exception as e:  # noqa: BLE001
            r, passed = f"<{type(e).__name__}: {e}>", False
        print(f"[test] {'PASS' if passed else 'FAIL'} {name}: {r!r}")
        ok = ok and passed
        return r

    check("tcl eval expr 6*7", lambda: sess.eval("expr 6*7", timeout=30))
    check("tcl version", lambda: sess.eval("info patchlevel", timeout=30))
    check("active design (before open)",
          lambda: sess.eval(sv._ACTIVE_DESIGN, timeout=60))
    parts = []

    def open_and_traverse():
        r = sv.open_design(SAMPLE)
        print(f"[test] open_design -> {r}")
        r = sv.list_parts()
        parts.extend([l for l in r.split("\n") if l.strip() and "|" in l])
        return f"{len(parts)} parts"
    check("open FULLADD.DSN + list_parts", open_and_traverse)

    if parts:
        refdes = parts[0].split("|")[0].strip()
        check(f"get_part_properties({refdes})",
              lambda: sv.get_part_properties(refdes))
        # set_part_property 走同一遍历 + 官方样例 API(SetEffectivePropStringValue),
        # 为保持本测试只读(退出不弹保存框),不在实时测试里改设计

    try:
        status[0].Quit()
        print("[test] Capture quit OK (nothing saved)")
    except Exception as e:  # noqa: BLE001
        print(f"[test] COM quit failed ({e}); killing Capture.exe")
        import subprocess
        subprocess.run(["taskkill", "/F", "/IM", "Capture.exe"], capture_output=True)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
