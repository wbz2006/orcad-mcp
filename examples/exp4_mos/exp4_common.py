# -*- coding: utf-8 -*-
"""Shared helpers for the Experiment 4 build (Capture Tcl bridge, port 5178)."""
import os
import sys
import threading
import time

os.environ.setdefault("ORCAD_MCP_PORT", "5178")
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "examples", "exp4_mos"))
import bridge as br  # noqa: E402

PROJ = r"D:\Users\Download\try"
DSN = os.path.join(PROJ, "exp4.dsn").replace("\\", "/")
PSP = "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/pspice"
CAPSYM = "C:/OrCAD/OrCAD_16.6_Lite/tools/capture/library/capsym.olb"

_DIALOG_REAPER = False


def start_dialog_reaper() -> None:
    global _DIALOG_REAPER
    if _DIALOG_REAPER:
        return
    _DIALOG_REAPER = True
    import win32gui
    import win32con

    def reaper():
        while True:
            time.sleep(1.0)
            try:
                def cb(hwnd, _):
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
                    btns = {t for _, t in kids}
                    if "recovered" in texts or "恢复" in texts:
                        want = ("否", "No")
                    elif "Save changes" in texts or "保存更改" in texts:
                        want = ("是", "Yes")
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

    status = []

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


def cap(code: str, timeout: float = 120.0) -> str:
    return br.BRIDGE.session().eval(code, timeout=timeout)


SETUP_TCL = r"""
if { [catch { set ::gExpSession $::DboSession_s_pDboSession }] } { error "no Dbo session" }
DboSession -this $::gExpSession

proc orCStr { s } { return [DboTclHelper_sMakeCString $s] }

proc orGetPage { {designSub "exp4"} {pageName "PAGE1"} } {
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
                while { $pg != $null } {
                    set pn [DboTclHelper_sMakeCString]
                    catch { $pg GetName $pn }
                    if { [string equal -nocase [DboTclHelper_sGetConstCharPtr $pn] $pageName] } {
                        catch { delete_DboSchematicPagesIter $pit }
                        set ::gGran [$pg GetPhysicalGranularity]
                        return $pg
                    }
                    set pg [$pit NextPage $st]
                }
                catch { delete_DboSchematicPagesIter $pit }
            }
        }
        set d [$it NextDesign $st]
    }
    error "design/page not found: $designSub/$pageName"
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
        set hs [$pin GetOffsetHotSpot $st]
        lappend out "$nm=[DboTclHelper_sGetCPointX $hs],[DboTclHelper_sGetCPointY $hs]"
        set pin [$it NextPin $st]
    }
    catch { delete_DboPartInstPinsIter $it }
    return $out
}
"""
