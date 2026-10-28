"""Experiment 3 builder — draws the BJT common-emitter amp in Capture via the MCP bridge.

用法: python draw_exp3.py <stage>
stages: create | open | probe | place | pins | route | props | save | check
"""

import os
import sys
import threading
import time

# ZCode 的 orcad-capture MCP 服务器可能已占用默认 5177,构建期改用 5178,
# Capture 由此环境变量继承(启动前设置),agent 会连到本脚本的 bridge。
os.environ.setdefault("ORCAD_MCP_PORT", "5178")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge as br  # noqa: E402
import exp3lib  # noqa: E402

PROJ = exp3lib.PROJ_DIR
DSN = os.path.join(PROJ, "exp3.dsn").replace("\\", "/")

PSP = "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice"
CAPSYM = "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/capsym.olb"

# 元件表: name, lib, pkg(partName), device, x, y, rotation  (rotation 0=默认, 90=旋转90)
PARTS = [
    # name      lib           pkg        device      x     y    rot
    ("Vs",      f"{PSP}/source.olb", "VSIN",     "VSIN",     1.2,  2.2, 0),
    ("Rs",      f"{PSP}/analog.olb", "R",        "R",        2.6,  3.4, 90),
    ("C1",      f"{PSP}/analog.olb", "C",        "C",        3.6,  3.4, 0),
    ("Rb1",     f"{PSP}/analog.olb", "R",        "R",        5.0,  5.6, 0),
    ("Rc",      f"{PSP}/analog.olb", "R",        "R",        6.6,  5.6, 0),
    ("Rb2",     f"{PSP}/analog.olb", "R",        "R",        5.0,  2.6, 0),
    ("Q1",      f"{PSP}/eval.olb",   "Q2N3904",  "Q2N3904",  5.9,  3.9, 0),
    ("Re",      f"{PSP}/analog.olb", "R",        "R",        6.9,  2.2, 0),
    ("Ce",      f"{PSP}/analog.olb", "C",        "C",        7.9,  2.2, 0),
    ("C2",      f"{PSP}/analog.olb", "C",        "C",        7.9,  4.6, 90),
    ("RL",      f"{PSP}/analog.olb", "R",        "R",        9.3,  3.4, 0),
    ("Vcc",     f"{PSP}/source.olb", "VDC",      "VDC",      8.9,  6.3, 0),
]

PROPS = {
    "Vs":  [("VOFF", "0"), ("VAMPL", "5mV"), ("FREQ", "1kHz")],
    "Rs":  [("VALUE", "1k")],
    "C1":  [("VALUE", "10u")],
    "Rb1": [("VALUE", "57k")],
    "Rc":  [("VALUE", "2k")],
    "Rb2": [("VALUE", "30k")],
    "Re":  [("VALUE", "1k")],
    "Ce":  [("VALUE", "47u")],
    "C2":  [("VALUE", "10u")],
    "RL":  [("VALUE", "2k")],
    "Vcc": [("DC", "12V")],
}


def cap(code: str, timeout: float = 120.0) -> str:
    return br.BRIDGE.session().eval(code, timeout=timeout)


_DIALOG_KILLER_STARTED = False


def start_dialog_reaper() -> None:
    """后台线程:自动点击 Capture 的 确定对话框(崩溃恢复/错误提示),防模态卡死."""
    global _DIALOG_KILLER_STARTED
    if _DIALOG_KILLER_STARTED:
        return
    _DIALOG_KILLER_STARTED = True

    import win32gui
    import win32con

    def reaper():
        import time as _t
        while True:
            _t.sleep(1.0)
            try:
                def cb(hwnd, _):
                    try:
                        if win32gui.GetClassName(hwnd) != "#32770":
                            return
                        if not win32gui.IsWindowVisible(hwnd):
                            return
                        title = win32gui.GetWindowText(hwnd)
                        if "OrCAD" not in title and "Capture" not in title:
                            return
                        kids = []
                        win32gui.EnumChildWindows(
                            hwnd, lambda w, _: kids.append((w, win32gui.GetWindowText(w))), None)
                        texts = " ".join(t for _, t in kids)
                        # 按语义+可用按钮判定
                        btns = {t for _, t in kids}
                        if "recovered" in texts:
                            want = ("否", "No")          # 丢弃恢复的垃圾工程
                        elif "Save changes" in texts or "保存更改" in texts:
                            want = ("是", "Yes")         # 保留已做的工作
                        elif "否" in btns or "No" in btns:
                            want = ("否", "No")
                        elif "确定" in btns or "OK" in btns:
                            want = ("确定", "OK")
                        else:
                            return
                        for w, txt in kids:
                            if any(t2 in txt for t2 in want):
                                win32gui.SendMessage(w, win32con.BM_CLICK, 0, 0)
                                break
                    except Exception:
                        pass
                win32gui.EnumWindows(cb, None)
            except Exception:
                pass

    threading.Thread(target=reaper, daemon=True).start()


def ensure_capture() -> None:
    start_dialog_reaper()
    br.BRIDGE.ensure()
    if br.BRIDGE.all_sessions():
        return
    import pythoncom
    import win32com.client

    status: list = []

    def go():
        pythoncom.CoInitialize()
        try:
            status.append(win32com.client.Dispatch("Capture.Application"))
        except Exception as e:  # noqa: BLE001
            status.append(e)

    t = threading.Thread(target=go, daemon=True)
    t.start()
    t.join(180)
    if status and isinstance(status[0], Exception):
        raise RuntimeError(f"COM Dispatch failed: {status[0]}")
    for _ in range(180):
        if br.BRIDGE.all_sessions():
            return
        time.sleep(1)
    raise RuntimeError("agent never connected")


SETUP_TCL = r"""
if { [catch { set ::gExpSession $::DboSession_s_pDboSession }] } { error "no Dbo session" }
DboSession -this $::gExpSession

proc orCStr { s } { return [DboTclHelper_sMakeCString $s] }

# 从 session 取回 exp3 设计的第一页(不依赖页面窗口是否打开)
proc orGetPage { {designSub "exp3"} } {
    set st [DboState]
    set it [$::gExpSession NewDesignsIter $st]
    set d [$it NextDesign $st]
    set null NULL
    while { $d != $null } {
        set nm [DboTclHelper_sMakeCString]
        catch { $d GetName $nm }
        if { [string match -nocase *$designSub* [DboTclHelper_sGetConstCharPtr $nm]] } {
            set vit [$d NewViewsIter $st $::IterDefs_SCHEMATICS]
            set v [$vit NextView $st]
            set sch [DboViewToDboSchematic $v]
            catch { delete_DboLibViewsIter $vit }
            if { $sch != $null } {
                set pit [$sch NewPagesIter $st]
                set pg [$pit NextPage $st]
                catch { delete_DboSchematicPagesIter $pit }
                if { $pg != $null } { set ::gGran [$pg GetPhysicalGranularity]; return $pg }
            }
        }
        set d [$it NextDesign $st]
    }
    error "design/page not found: $designSub"
}

proc orPlacePart { page libPath pkg partName device name x y {rot 0} } {
    set st [DboState]
    set lib [$::gExpSession GetLib [orCStr $libPath] $st]
    if { $lib == "NULL" } { error "GetLib failed: $libPath" }
    if { [string first "." $partName] < 0 } { set partName "$partName.Normal" }
    set p [$lib GetPart [orCStr $partName] $st]
    if { $p == "NULL" } { error "GetPart failed: $partName" }
    if { [string first "." $pkg] < 0 } { set pkg "$pkg.Normal" }
    set xd [expr { round($x * $::gGran) }]
    set yd [expr { round($y * $::gGran) }]
    set loc [DboTclHelper_sMakeCPoint $xd $yd]
    if { $rot eq "0" } {
        set inst [$page NewPlacedInst $st [orCStr $name] [orCStr $pkg] $p [orCStr $device] $loc]
    } else {
        set inst [$page NewPlacedInst $st [orCStr $name] [orCStr $pkg] $p [orCStr $device] $loc $rot]
    }
    if { $inst == "NULL" } { error "NewPlacedInst failed: $name" }
    return $inst
}

proc orSetActiveProp { inst pname pval } {
    set st [DboState]
    $inst SetEffectivePropStringValue [orCStr $pname] [orCStr $pval]
    if { [$st OK] != 1 } { error "SetEffectivePropStringValue $pname=$pval failed" }
    return "ok"
}

proc orPinList { inst } {
    set st [DboState]
    set out {}
    set it [$inst NewPinsIter $st]
    set pin [$it NextPin $st]
    set null NULL
    while { $pin != $null } {
        set nm "?"
        catch { set c [DboTclHelper_sMakeCString]; $pin GetName $c; set nm [DboTclHelper_sGetConstCharPtr $c] }
        set loc "?"
        foreach m {GetLocation GetPinLocation GetStartPoint} {
            foreach args {"" "st"} {
                set ok 0
                if { $args == "" } {
                    if { ![catch { set l [$pin $m] }] && $l != "" && $l != "NULL" } { set ok 1 }
                } else {
                    if { ![catch { set l [$pin $m $st] }] && $l != "" && $l != "NULL" } { set ok 1 }
                }
                if { $ok } {
                    set x "?"
                    set y "?"
                    catch { set x [DboTclHelper_sGetCPointX $l] }
                    catch { set y [DboTclHelper_sGetCPointY $l] }
                    if { $x ne "?" } { set loc "$m:$x,$y"; break }
                }
            }
            if { $loc ne "?" } { break }
        }
        lappend out "$nm=$loc"
        set pin [$it NextPin $st]
    }
    catch { delete_DboPartInstPinsIter $it }
    return $out
}
"""


def stage_create() -> None:
    import subprocess
    subprocess.run(["taskkill", "/F", "/IM", "Capture.exe"], capture_output=True)
    time.sleep(2)
    ensure_capture()
    if os.path.exists(DSN):
        os.remove(DSN)
        print("removed old", DSN)
    exp3lib.generate_all("bias")
    # 枚举解释器里的关键常量,确认枚举名
    print(cap("lsort [info commands ::DboValue_*]"))
    print(cap("lsort [info commands ::*ROTATE*]; lsort [info commands ::IterDefs_*]"))
    code = SETUP_TCL + r'''
set _st [DboState]
set _d [$::gExpSession CreateDesign $_st [orCStr "%DSN%"] [orCStr "SCHEMATIC1"]]
if { $_d == "NULL" } { error "CreateDesign failed" }
set _viter [$_d NewViewsIter $_st $::IterDefs_SCHEMATICS]
set _v [$_viter NextView $_st]
set _sch [DboViewToDboSchematic $_v]
if { $_sch == "NULL" } { error "no schematic" }
set _pg [$_sch NewPage $_st [orCStr "PAGE1"]]
if { $_pg == "NULL" } { error "NewPage failed" }
set ::gExpPage $_pg
set _sst [$::gExpSession SaveDesign $_d]
if { [catch { $_sst OK } ok] } { set ok "?" }
return "design+page created, save ok=$ok"
'''.replace("%DSN%", DSN)
    print(cap(code, timeout=180))


def stage_open() -> None:
    ensure_capture()
    print(cap(f'Open {{D:\\Users\\Download\\exp3_BJT_CE\\exp3.opj}}', timeout=180))
    print(cap('after 1000; NDesign; NSchematic {SCHEMATIC1}; NPage {SCHEMATIC1} {PAGE1}; return "navigated"', timeout=60))
    # 激活页对象
    print(cap(SETUP_TCL + '''
set ::gExpPage [GetActivePage]
if { $::gExpPage == "NULL" || $::gExpPage == "" } { error "no active page" }
set nm [DboTclHelper_sMakeCString]
catch { $::gExpPage GetName $nm }
return "active page: [DboTclHelper_sGetConstCharPtr $nm]"
'''))
    print(cap("GetActiveDesign"))


CREATE_TCL = r"""
set _st [DboState]
set _d [$::gExpSession CreateDesign $_st [orCStr "%DSN%"] [orCStr "SCHEMATIC1"]]
if { $_d == "NULL" } { error "CreateDesign failed (design may already exist)" }
set _viter [$_d NewViewsIter $_st $::IterDefs_SCHEMATICS]
set _v [$_viter NextView $_st]
set _sch [DboViewToDboSchematic $_v]
if { $_sch == "NULL" } { error "no schematic" }
set _pg [$_sch NewPage $_st [orCStr "PAGE1"]]
if { $_pg == "NULL" } { error "NewPage failed" }
set ::gExpPage $_pg
set ::gExpDesign $_d
return "design+page created in session"
"""


def stage_bootstrap() -> None:
    import subprocess
    subprocess.run(["taskkill", "/F", "/IM", "Capture.exe"], capture_output=True)
    time.sleep(2)
    if os.path.exists(DSN):
        os.remove(DSN)
        print("removed old dsn")
    exp3lib.generate_all(None)  # 无 ActiveProfile:打开工程不触发 profile 初始化
    ensure_capture()
    print(cap(SETUP_TCL + CREATE_TCL.replace("%DSN%", DSN), timeout=180))
    assert os.path.exists(DSN.replace("/", "\\")), "dsn missing on disk after save!"
    print("dsn on disk OK")
    print(cap(r'Open {D:\Users\Download\exp3_BJT_CE\exp3.opj}', timeout=240))
    time.sleep(3)
    print(cap('NDesign; NSchematic {SCHEMATIC1}; NPage {SCHEMATIC1} {PAGE1}; return "nav ok"', timeout=120))
    print(cap(SETUP_TCL + r'''
set pg [GetActivePage]
if { $pg == "NULL" || $pg == "" } { error "no active page" }
set nm [DboTclHelper_sMakeCString]
catch { $pg GetName $nm }
return "active page: [DboTclHelper_sGetConstCharPtr $nm]"
''', timeout=60))


def stage_probe() -> None:
    ensure_capture()
    # 放一个探针电阻,验证 PlacePart 用户命令语义(页面窗口已激活)
    r = cap(SETUP_TCL + f'''
if {{ [catch {{ PlacePart 4.0 5.0 "{PSP}/analog.olb" "R" "R" "" }} e] }} {{ return "PlacePart err: $e" }}
return "PlacePart ok"
''', timeout=60)
    print(r)
    print(cap(SETUP_TCL + '''
set pg [GetActivePage]
set st [DboState]
set out {}
set it [$pg NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $null } {
        set rn [DboTclHelper_sMakeCString]
        catch { $pl GetReference $rn }
        set loc "?"
        catch { set lc [$pl GetLocation $st]; set loc "[DboTclHelper_sGetCPointX $lc],[DboTclHelper_sGetCPointY $lc]" }
        lappend out "[DboTclHelper_sGetConstCharPtr $rn]@$loc"
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return "instances: $out"
''', timeout=60))
    print(cap(SETUP_TCL + '''
set ::gExpPage [GetActivePage]
set st [DboState]
set out {}
set it [$::gExpPage NewPartInstsIter $st]
set i [$it NextPartInst $st]
set null NULL
while { $i != $null } {
    set pl [DboPartInstToDboPlacedInst $i]
    if { $pl != $null } {
        set rn [DboTclHelper_sMakeCString]
        catch { $pl GetReference $rn }
        lappend out [DboTclHelper_sGetConstCharPtr $rn]
    }
    set i [$it NextPartInst $st]
}
catch { delete_DboPagePartInstsIter $it }
return "instances: $out"
'''))


if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "create"
    globals()[f"stage_{stage}"]()
    print(f"[stage {stage}] done")
