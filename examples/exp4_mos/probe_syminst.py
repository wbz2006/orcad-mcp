# -*- coding: utf-8 -*-
"""Probe DboPage method table + enumerate symbol insts (grounds)."""
import sys, os, time
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import win32gui, win32con
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
os.environ.setdefault("ORCAD_MCP_PORT", sys.argv[1] if len(sys.argv) > 1 else "5178")
import bridge as br


def frame():
    res = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in win32gui.GetWindowText(h):
            res.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return res[0]


PROBE = r'''
proc probeP1 {} {
    set out {}
    set st [DboState]
    set pg [GetActivePage]
    # 1) full method table
    if { [catch { $pg ZZZBogus } e] } {
        foreach m [lsort $e] {
            if { [string match -nocase "*iter*" $m] || [string match -nocase "*symbol*" $m]
                 || [string match -nocase "*global*" $m] || [string match -nocase "*count*" $m] } {
                lappend out "M $m"
            }
        }
    }
    lappend out "---try symbol/globals iters---"
    foreach name {NewGlobalsIter NewSymbolInstsIter NewGlobalSymsIter} {
        if { ![catch { set it [$pg $name $st] } e2] } {
            lappend out "OK $name"
            # try to iterate
            set n 0
            set g [$it NextGlobal $st]
            while { $g != "NULL" && $n < 40 } {
                incr n
                set id "?"
                catch { set id [$g GetId $st] }
                set l "?"
                catch {
                    set l [$g GetLocation $st]
                    set l [DboTclHelper_sGetCPointX $l],[DboTclHelper_sGetCPointY $l]
                }
                set nm "?"
                catch {
                    set c [DboTclHelper_sMakeCString]
                    $g GetName $c
                    set nm [DboTclHelper_sGetConstCharPtr $c]
                }
                lappend out "  G id=$id name=$nm loc=$l"
                set g [$it NextGlobal $st]
            }
            lappend out "  count=$n"
            catch { delete_DboGlobalsIter $it }
        } else {
            lappend out "FAIL $name : $e2"
        }
    }
    return $out
}
if { [catch { probeP1 } r] } { return "ERR: $r" }
return $r
'''


def main():
    f = frame()
    s = None
    for _ in range(15):
        try:
            s = br.BRIDGE.session(); break
        except Exception:
            time.sleep(1)
    assert s, "no agent"
    try:
        s.eval("SelectPMItem {PAGE1}", 60)
        win32gui.PostMessage(win32gui.EnumChildWindows(f, lambda h, _: True, None) and 0 or 0, 0, 0, 0)
    except Exception:
        pass
    # activate page via tree enter
    out = []
    win32gui.EnumChildWindows(f, lambda h, _: out.append(h) if win32gui.GetClassName(h) == "SysTreeView32" else None, None)
    for t in out:
        win32gui.PostMessage(t, win32con.WM_SETFOCUS, 0, 0)
        win32gui.PostMessage(t, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        win32gui.PostMessage(t, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        time.sleep(1.0)
    s.eval("GetActivePage", 30)
    r = s.eval(PROBE, 60)
    if isinstance(r, list):
        print("\n".join(r))
    else:
        print(r)


if __name__ == "__main__":
    main()
