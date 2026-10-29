# -*- coding: utf-8 -*-
"""Delete PAGE2-5 from EXP4.DSN via pywinauto (agentless, no TCL -> no crashes)."""
import sys, os, time, subprocess, re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys

CAPTURE = r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\Capture.exe"
DSN = r"D:\Users\Download\try\EXP4.DSN"
ZOMBIES = {"40484", "51440", "1524"}


def pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Capture.exe", "/FO", "CSV"],
                         capture_output=True).stdout.decode("gbk", errors="replace")
    return [p for p in re.findall(r'"Capture.exe","(\d+)"', out) if p not in ZOMBIES]


def handle_wizard(app, rounds=30):
    """Dismiss 'Select Project Type' wizard and any stray dialogs."""
    for _ in range(rounds):
        handled = False
        for w in Desktop(backend="win32").windows():
            try:
                if not w.is_visible():
                    continue
                title = w.window_text()
            except Exception:
                continue
            if not title:
                continue
            if "Select Project Type" in title:
                print("  wizard:", title, flush=True)
                try:
                    w.child_window(title="Analog or Mixed", control_type="",
                                   class_name_re="Button").click_input()
                    time.sleep(0.5)
                except Exception as e:
                    print("   radio err:", e, flush=True)
                try:
                    w.child_window(title="OK", class_name="Button").click_input()
                except Exception as e:
                    print("   ok err:", e, flush=True)
                handled = True
                time.sleep(1.5)
            elif w.class_name() == "#32770" and title not in ("OrCAD Capture",):
                print("  dialog:", title, flush=True)
                for btn in ("是(&Y)", "Yes", "确定", "OK", "否(&N)", "No"):
                    try:
                        w.child_window(title=btn, class_name="Button").click_input()
                        handled = True
                        time.sleep(1.0)
                        break
                    except Exception:
                        continue
        if not handled:
            return
        time.sleep(1)


def dump_tree(tree, indent=1):
    for r in tree.roots():
        def rec(item, d):
            print("  " * (d + 1) + item.text(), flush=True)
            if item.children():
                item.expand()
                for c in item.children():
                    rec(c, d + 1)
        rec(r, 0)


def main():
    live = pids()
    if live:
        print("attach to existing Capture pid(s):", live, flush=True)
        app = Application(backend="win32").connect(process=live[0])
    else:
        print("launching Capture...", flush=True)
        app = Application(backend="win32").start(CAPTURE + " " + DSN)
        time.sleep(10)
        handle_wizard(app)

    main_win = None
    for i in range(40):
        try:
            for w in app.windows():
                if "OrCAD Capture" in w.window_text():
                    main_win = w
                    break
        except Exception:
            pass
        if main_win:
            break
        handle_wizard(app, rounds=2)
        time.sleep(3)
    if not main_win:
        print("FATAL: no Capture frame", flush=True)
        return 1
    print("frame:", main_win.window_text(), flush=True)

    tree = None
    for i in range(30):
        try:
            cands = main_win.descendants(class_name="SysTreeView32")
            if cands:
                tree = cands[0]
                print(f"tree found at t={i * 2}s", flush=True)
                break
        except Exception:
            pass
        handle_wizard(app, rounds=2)
        time.sleep(2)
    if not tree:
        print("FATAL: no tree", flush=True)
        return 1

    print("--- tree dump ---", flush=True)
    dump_tree(tree)

    # delete PAGE2..5
    for pg in ["PAGE2", "PAGE3", "PAGE4", "PAGE5"]:
        target = None
        for r in tree.roots():
            stack = [r]
            while stack:
                it = stack.pop()
                if it.text().strip() == pg:
                    target = it
                    break
                stack.extend(it.children())
        if not target:
            print(f"{pg}: absent (ok)", flush=True)
            continue
        target.select()
        time.sleep(0.8)
        tree.set_focus()
        time.sleep(0.4)
        m0 = os.path.getmtime(DSN)
        send_keys("{DELETE}")
        time.sleep(1.5)
        # confirm dialog?
        for _ in range(4):
            done = True
            for w in Desktop(backend="win32").windows():
                try:
                    if w.is_visible() and w.class_name() == "#32770" and w.window_text():
                        done = False
                        print(f"  {pg} confirm:", w.window_text(), flush=True)
                        for btn in ("是(&Y)", "Yes", "确定", "OK"):
                            try:
                                w.child_window(title=btn, class_name="Button").click_input()
                                time.sleep(1.0)
                                break
                            except Exception:
                                continue
                except Exception:
                    pass
            if done:
                break
            time.sleep(1.5)
        # verify
        still = False
        for r in tree.roots():
            stack = [r]
            while stack:
                it = stack.pop()
                if it.text().strip() == pg:
                    still = True
                    break
                stack.extend(it.children())
        print(f"{pg}: deleted={not still}", flush=True)

    print("--- tree after ---", flush=True)
    dump_tree(tree)

    # save
    main_win.set_focus()
    time.sleep(0.5)
    m0 = os.path.getmtime(DSN)
    send_keys("^s")
    saved = False
    for _ in range(12):
        time.sleep(1)
        try:
            handle_wizard(app, rounds=2)
        except Exception:
            pass
        if os.path.getmtime(DSN) != m0:
            saved = True
            break
    print("SAVED" if saved else "save FAILED", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
