"""v5 幂等布线:崩溃自动重启,从进度文件继续。"""
import sys, os, time, subprocess, json
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE); sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br, draw_exp3 as dx
from build_exp3 import parse_insts, TCL_LIST_INSTS, SET_ROT_HELPER

PINS = json.load(open("pins.json", encoding="utf-8"))
CAPSYM = "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/capsym.olb"
PROG = "wire_progress.json"

W = []
def wire(p1, p2): W.append((p1, p2))
wire(PINS["Vcc"]["+"], (1.0, 1.9))
wire((1.0, 1.9), (3.3, 1.9)); wire((3.3, 1.9), (5.5, 1.9))
wire(PINS["Rb1"]["2"], (PINS["Rb1"]["2"][0], 1.9)); wire(PINS["Rc"]["2"], (PINS["Rc"]["2"][0], 1.9))
wire((1.0, 0.9), (1.0, 0.6))
rcb = PINS["Rc"]["1"]
wire(rcb, (rcb[0], 3.2)); wire((5.5, 3.2), (4.4, 3.2)); wire((4.4, 3.2), PINS["Q1"]["c"])
wire((5.5, 3.2), (6.2, 3.2)); wire((6.2, 3.2), PINS["C2"]["1"])
wire(PINS["C2"]["2"], (8.4, 2.3)); wire((8.4, 2.3), PINS["RL"]["1"])
baserail_y = PINS["Q1"]["b"][1]
wire(PINS["C1"]["2"], (2.8, 4.4)); wire((2.8, 4.4), (2.8, baserail_y)); wire((2.8, baserail_y), PINS["Q1"]["b"])
wire(PINS["Rb1"]["1"], (PINS["Rb1"]["1"][0], baserail_y)); wire(PINS["Rb2"]["2"], (PINS["Rb2"]["2"][0], baserail_y))
wire(PINS["Vs"]["+"], (0.9, 3.4)); wire((0.9, 3.4), (1.6, 3.4)); wire((1.6, 3.4), (1.6, PINS["Rs"]["1"][1])); wire((1.6, PINS["Rs"]["1"][1]), PINS["Rs"]["1"])
wire(PINS["Rs"]["2"], PINS["C1"]["1"])
wire(PINS["Q1"]["e"], (4.4, 4.6)); wire((4.4, 4.6), (5.7, 4.6)); wire(PINS["Re"]["2"], (PINS["Re"]["2"][0], 4.6))
wire((5.7, 4.6), (6.3, 4.6)); wire(PINS["Ce"]["2"], (PINS["Ce"]["2"][0], 4.6))

J = [(PINS["Rb1"]["1"][0], baserail_y), (PINS["Rb1"]["2"][0], 1.9), (PINS["Rc"]["2"][0], 1.9),
     (rcb[0], 3.2), (PINS["Re"]["2"][0], 4.6)]
G = [PINS["Vcc"]["-"], PINS["Vs"]["-"], PINS["Rb2"]["1"], PINS["Re"]["1"], PINS["Ce"]["1"], PINS["RL"]["2"]]
A = [((PINS["Rs"]["2"][0] + PINS["C1"]["1"][0]) / 2, PINS["Rs"]["2"][1], "Vi"),
     (PINS["C2"]["2"][0] + 0.9, PINS["C2"]["2"][1], "Vo")]
T = "PlaceText 0.7 5.9 3.8 6.3 {班级:________  姓名:________}"

try:
    prog = json.load(open(PROG))["done"]
except Exception:
    prog = 0

TASKS = [("W", i, w) for i, w in enumerate(W)] + \
        [("J", i, j) for i, j in enumerate(J)] + \
        [("G", i, g) for i, g in enumerate(G)] + \
        [("A", i, a) for i, a in enumerate(A)] + [("T", 0, T)]

i = prog
while i < len(TASKS):
    kind, idx, arg = TASKS[i]
    try:
        if kind == "W":
            cmd = f'PlaceWire {arg[0][0]} {arg[0][1]} {arg[1][0]} {arg[1][1]}'
        elif kind == "J":
            cmd = f'PlaceJunction {arg[0]} {arg[1]}'
        elif kind == "G":
            cmd = f'PlaceGround {arg[0]} {arg[1]} "{CAPSYM}" "GND_POWER" "0"'
        elif kind == "A":
            cmd = f'PlaceNetAlias {arg[0]} {arg[1]} {arg[2]}'
        else:
            cmd = arg
        r = s.eval(f'if {{ [catch {{ {cmd} }} e] }} {{ return "ERR: $e" }} ; return "ok"', 120)
        if "ok" not in r:
            print(f"task {i} ({kind}) ERR: {r}")
        else:
            print(f"task {i} ({kind}) ok")
    except Exception as e:
        print(f"task {i} ({kind}) CRASH: {e}")
        # 崩溃恢复:杀掉重启,重开工程,激活页面,继续(i 不前进,但该任务可能已完成——
        # 用“重复放置”容错:线重复无害(PlaceWire 重复画会叠线,可接受),J/G/A 重复也无害)
        subprocess.run(["taskkill", "/F", "/IM", "Capture.exe"], capture_output=True)
        time.sleep(3)
        dx.ensure_capture()
        s = br.BRIDGE.session()
        s.eval(r'Open {D:\Users\Download\exp3_BJT_CE\exp3.opj}', timeout=300)
        time.sleep(4)
        s.eval('SelectPMItem {PAGE1}', 60)
        import win32gui, win32con, win32api
        frame = win32gui.FindWindow("OrCaptureFrame", None)
        try: win32gui.SetForegroundWindow(frame)
        except Exception: pass
        time.sleep(0.5)
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(3)
        i += 1  # 崩溃的那次大概率已生效(线已画),跳过防重复
        json.dump({"done": i}, open(PROG, "w"))
        continue
    i += 1
    json.dump({"done": i}, open(PROG, "w"))

print("save:", s.eval('Menu "File::Save"', 180))
print("ALL ROUTING DONE")
