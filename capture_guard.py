"""capture_guard.py — Capture 卡顿/意外弹窗的系统性防护。

背景:自动化中最常见的"卡很久"都是同一类根因 ——
  (a) 模态对话框饿死 Capture 主线程/agent 定时器 → 每次 eval 白等 30s 超时;
  (b) 主窗口真假死(IsHungAppWindow)→ 任何消息都无响应,只能走恢复路径;
  (c) 僵尸 Capture 进程/残留 .DSNlck 干扰下一次操作;
  (d) 保存被对话框或死锁挡住,脚本却继续跑,错误滞后爆发。

本模块把处置收敛成四个原语,自动化脚本应全程使用:
  eval_safe(s, tcl)      超时→收割意外弹窗→重试;agent 断线→等自愈;TCL 错误→立即抛
  reap(expected)         枚举 Capture 进程名下的 #32770,按已知语义点按钮(可排除"预期弹窗")
  save_verified(s, path) Menu File::Save + .DSN mtime 核验,保存被挡时给出诊断
  health([opj])          进程/假死/僵尸/锁文件/agent RTT 一屏体检

CLI:
  python capture_guard.py health [EXP4.DSN路径]
  python capture_guard.py reap [--dry]
"""
import os
import re
import sys
import time
import glob
import ctypes
import subprocess

import win32gui
import win32con
import win32process

_u32 = ctypes.windll.user32
SMTO_ABORTIFHUNG = 0x0002


def _pid(h):
    return win32process.GetWindowThreadProcessId(h)[1]

# 打印/另存/打开是"流程预期弹窗",收割时永远跳过(点错会毁掉进行中的打印/保存流程)
EXPECTED_TITLES = ("打印", "Print", "另存为", "Save As", "保存", "打开", "Open",
                   "页面设置", "Page Setup", "PSpice", "Probe")


# ---- 进程/窗口探测 ----------------------------------------------------------

def capture_pids():
    """拥有可见 'OrCAD Capture' 顶层窗口的进程 pid 集合。"""
    pids = set()
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in win32gui.GetWindowText(h):
            pids.add(_pid(h))
        return True
    win32gui.EnumWindows(cb, None)
    return pids


def exe_pids(image="Capture.exe"):
    """当前所有该映像名的进程 pid(含僵尸)。tasklist 慢(~0.5s),健康检查专用。"""
    out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {image}",
                          "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
    return set(int(m) for m in re.findall(r'"Capture\.exe",(\d+)', out))


def is_hung(hwnd):
    return bool(_u32.IsHungAppWindow(hwnd))


def hung_frames():
    return [h for h in frames() if is_hung(h)]


def frames():
    out = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and "OrCAD Capture" in win32gui.GetWindowText(h):
            out.append(h)
        return True
    win32gui.EnumWindows(cb, None)
    return out


def dialogs(pid_filter=None):
    """可见 #32770 对话框,(hwnd, title, pid, buttons[(ctrlid, text)])."""
    pids = pid_filter if pid_filter is not None else capture_pids()
    out = []
    def cb(h, _):
        if not win32gui.IsWindowVisible(h) or win32gui.GetClassName(h) != "#32770":
            return True
        pid = _pid(h)
        if pid_filter is not None and pid not in pids:
            return True
        btns = [(win32gui.GetDlgCtrlID(w), win32gui.GetWindowText(w))
                for w in _children(h) if win32gui.GetClassName(w) == "Button"]
        out.append((h, win32gui.GetWindowText(h), pid, btns))
        return True
    win32gui.EnumWindows(cb, None)
    return out


def _children(h):
    out = []
    def cb(w, _):
        out.append(w)
        return True
    try:
        win32gui.EnumChildWindows(h, cb, None)
    except win32gui.error:
        pass
    return out


def locks_for(path):
    """给定 .DSN/.opj 路径,返回残留锁文件(实验实证: 'EXP4.DSN'+'lck')。"""
    return [p for p in glob.glob(path + "lck*") if os.path.exists(p)]


# ---- 消息发送(永不裸 SendMessage 到可能假死的窗口) --------------------------

def _msg(h, msg, wp=0, lp=0, timeout_ms=3000):
    res = ctypes.c_longlong(0)
    ok = _u32.SendMessageTimeoutW(h, msg, wp, lp, SMTO_ABORTIFHUNG, timeout_ms,
                                  ctypes.byref(res))
    return ok, res.value


def click_button(hwnd, ctrlid=None):
    """BM_CLICK 走 SendMessageTimeoutW;目标假死时 3s 放弃而不是挂死自己。"""
    targets = [w for w in _children(hwnd) if win32gui.GetClassName(w) == "Button"
               and (ctrlid is None or win32gui.GetDlgCtrlID(w) == ctrlid)]
    if not targets:
        return False
    _msg(targets[0], win32con.BM_CLICK)
    return True


# ---- 弹窗收割 ----------------------------------------------------------------

def reap(expected=EXPECTED_TITLES, save_changes=True, dry=False):
    """收割 Capture 名下的"意外"模态弹窗。返回 [(title, action)]。

    语义表(全部为实证结论,见 skill api-notes):
      ORCAP-1680(是/否)      → 否(不恢复未保存修改,加载磁盘态)
      上次异常关闭(确定/取消) → 确定(加载磁盘态)
      Save changes(是/否)    → save_changes(默认是,保住已改内容)
      崩溃报告/已停止工作     → 关闭/Close
      其余                    → IDOK(1),没有再点第一个按钮
    标题命中 expected(打印/另存为/打开…)的不动 —— 那是流程自己的弹窗。
    """
    taken = []
    for h, title, pid, btns in dialogs():
        if any(x.lower() in title.lower() for x in expected):
            continue
        texts = [t for _, t in btns]
        joined = title + " | " + " | ".join(texts)
        action = None
        if "ORCAP-1680" in title:
            # IDNO=7:是/否恢复询问,自动选"否"=加载磁盘态
            action = ("否", 7) if any("否" in t or re.match(r"^No\b", t) for t in texts) else (None, 7)
        elif "recovered" in joined.lower() or "恢复" in joined:
            action = ("否", 7)
        elif "save changes" in joined.lower() or "保存更改" in joined:
            action = ("是" if save_changes else "否", 6 if save_changes else 7)
        elif ("已停止工作" in joined or "stopped working" in joined.lower()
              or "report" in title.lower()):
            action = ("关闭", 8)  # IDCLOSE
        else:
            action = (None, 1)  # 默认 IDOK
        label, ctrlid = action
        if dry:
            taken.append((title, f"DRY would click {label or ('IDOK' if ctrlid==1 else ctrlid)}"))
            continue
        ok = False
        if label is not None:
            for w in _children(h):
                if win32gui.GetClassName(w) == "Button" and label in win32gui.GetWindowText(w):
                    _msg(w, win32con.BM_CLICK)
                    ok = True
                    break
        if not ok and ctrlid is not None:
            ok = click_button(h, ctrlid)
        if not ok and ctrlid is None and btns:
            ok = click_button(h, ctrlid=btns[0][0])
        taken.append((title, f"clicked {label or ctrlid}" if ok else "NO BUTTON MATCHED"))
    return taken


def _first_button(h):
    for w in _children(h):
        if win32gui.GetClassName(w) == "Button":
            return w
    return 0


# ---- eval 硬超时 --------------------------------------------------------------

def eval_safe(s, tcl, timeout=20.0, retries=2):
    """带自动恢复的 eval。策略:
    - 超时 → 大概率模态框饿死 agent → reap → 重试(每次都先把意外弹窗清掉);
    - agent disconnected → agent 会 4s 自愈重连,ping 等回来再试;
    - TCL error → 确定性脚本错误,立即抛(重试无意义,别浪费 20s×N)。
    彻底失败时抛出的异常带诊断(残余弹窗/假死/僵尸),直接指到恢复路径。
    """
    last = None
    for attempt in range(retries + 1):
        try:
            return s.eval(tcl, timeout=timeout)
        except TimeoutError as e:
            last = e
            taken = reap()
            print(f"[guard] eval 超时(第{attempt+1}次),收割弹窗: {taken or '无'}")
            if not taken:
                hung = hung_frames()
                if hung:
                    raise RuntimeError(
                        f"Capture 主窗口假死(IsHungAppWindow) hwnd={hung};"
                        f"消息路径已无效,走恢复: taskkill /IM Capture.exe /F → 删 .DSNlck → cap_open.py") from e
        except RuntimeError as e:
            msg = str(e)
            if msg.startswith("TCL error"):
                raise
            last = e
            if "disconnected" in msg:
                ok = _wait_agent_back(s, 12)
                print(f"[guard] agent 断线,{'' if ok else '未'}恢复连接")
                if not ok:
                    break
            else:
                raise
    leftover = [(t, b) for _, t, _, b in dialogs()] if capture_pids() else []
    raise RuntimeError(
        f"eval_safe 彻底失败: {last!r}; 残余弹窗={残}; "
        f"处置阶梯: reap → health 查假死/僵尸 → taskkill+删锁+cap_open.py 重启")


def _wait_agent_back(s, seconds):
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            if s.ping(timeout=3):
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


# ---- 保存核验 ----------------------------------------------------------------

def save_verified(s, dsn_path, timeout=40.0, settle=10.0):
    """Menu File::Save(带弹窗恢复)→ 以 .DSN mtime 核验保存是否落盘。

    返回 'saved'(mtime 前进) / 'no-change'(eval 成功但 mtime 未动,
    多为无修改可存) / 抛异常(保存被挡或超时,异常里带诊断)。
    """
    m0 = os.path.getmtime(dsn_path) if os.path.exists(dsn_path) else 0
    eval_safe(s, 'Menu "File::Save"', timeout=timeout)
    t0 = time.time()
    while time.time() - t0 < settle:
        if os.path.exists(dsn_path) and os.path.getmtime(dsn_path) > m0:
            return "saved"
        time.sleep(0.5)
    leftover = [(t, [bt for _, bt in b]) for _, t, _, b in dialogs()]
    if leftover:
        raise RuntimeError(
            f"保存后 mtime 未前进,且存在弹窗 {leftover};"
            f"若是 另存为/Save As = 设计未命名或路径问题,需流程显式指定路径;其余先 reap")
    return "no-change"


# ---- 健康检查 ----------------------------------------------------------------

def health(opj=None, port=None):
    rep = {}
    rep["frames"] = [(h, win32gui.GetWindowText(h)[:60],
                      _pid(h)) for h in frames()]
    rep["hung"] = hung_frames()
    live = capture_pids()
    rep["zombies"] = sorted(exe_pids() - live)
    rep["dialogs"] = [(t, [bt for _, bt in b]) for _, t, _, b in dialogs(live)]
    if opj:
        lk = locks_for(opj)
        # Capture 正在运行时的锁是正常态;没有运行进程的锁才是残留
        rep["locks"] = [p + ("(Capture运行中,正常)" if live else "(无Capture进程=残留,先删)") for p in lk]
    port = port or int(os.environ.get("ORCAD_MCP_PORT", "5177"))
    try:
        import bridge as br
        try:
            b = br.Bridge(port)
            b.ensure()
        except OSError as e:
            if "10048" in str(e):
                rep["agent"] = f"端口 {port} 被占用(MCP server/另一 bridge 在跑):用该端口的既有会话或 MCP 工具,或改用其他端口"
                return rep
            raise
        t0 = time.time()
        ok = False
        while time.time() - t0 < 8:
            try:
                if b.session().ping(timeout=3):
                    ok = True
                    break
            except Exception:
                time.sleep(1)
        rep["agent"] = f"ping={'OK' if ok else 'FAIL'}(等agent回连{time.time()-t0:.1f}s) port={port}"
    except Exception as e:
        rep["agent"] = f"FAIL {e!r}"
    return rep


def _print_report(rep):
    for k, v in rep.items():
        print(f"{k:9s}: {v}")
    stale_locks = [p for p in rep.get("locks", []) if "残留" in p]
    agent_bad = str(rep.get("agent", "")).startswith("FAIL")
    bad = rep["hung"] or rep["zombies"] or stale_locks or agent_bad
    print("结论:", "有异常,先按上面处置再跑自动化" if bad else "健康")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "health"
    if cmd == "health":
        _print_report(health(sys.argv[2] if len(sys.argv) > 2 else None))
    elif cmd == "reap":
        dry = "--dry" in sys.argv
        print(reap(dry=dry) or "无意外弹窗")
    else:
        print(__doc__)
