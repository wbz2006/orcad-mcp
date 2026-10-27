"""OrCAD Capture 16.6 MCP server (ZCode).

AI 直接操作 OrCAD Capture 的 MCP 接口。链路:
    ZCode --(MCP stdio)--> server.py --(TCP 127.0.0.1:5177)--> TCL agent (Capture 进程内)
agent 由 <CDSROOT>\\tools\\capture\\tclscripts\\capAutoLoad\\orcad_mcp_agent.tcl 提供。

工具分四层:
  1) 高层语义工具: list_designs / list_pages / list_parts / get_part_properties /
     set_part_property / open_design / save_design / run_menu
  2) 万能通道:    tcl_eval —— 在 Capture 内执行任意 TCL(Dbo API 全量可用)
  3) API 检索:    tcl_api_search —— 在提取的官方 Tcl/Tk Extensions 手册中查命令
  4) COM 兜底:    com_launch_capture / com_quit_capture
"""

from __future__ import annotations

import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bridge as br  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
DEFAULT_TIMEOUT = 120.0
MAX_LINES = 2000

mcp = FastMCP("orcad-capture")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def tcl_quote(s: str) -> str:
    """Quote a python string as a safe TCL double-quoted string."""
    return '"' + (
        s.replace("\\", "\\\\").replace('"', '\\"')
        .replace("$", "\\$").replace("[", "\\[").replace("]", "\\]")
    ) + '"'


def _cap(code: str, timeout: float = DEFAULT_TIMEOUT, pid: int | None = None) -> str:
    sess = br.BRIDGE.session(pid)
    return sess.eval(code, timeout=timeout)


def _clip(text: str, max_lines: int = MAX_LINES) -> str:
    lines = text.split("\n")
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines truncated)"


_ACTIVE_DESIGN = r"""
if { [catch { set _s $::DboSession_s_pDboSession }] } { return "no Capture Dbo session yet (is Capture fully started?)" }
DboSession -this $_s
set _d [$_s GetActiveDesign]
if { $_d == "NULL" } { return "no design open" }
set _n [DboTclHelper_sMakeCString]
catch { $_d GetName $_n }
DboTclHelper_sGetConstCharPtr $_n
"""

# Dbo traversal over designs -> schematics -> pages; %PAGE_BODY% runs per page
# with these variables in scope: _dname, _sname, _pname (+ _s, _st, _null, _out).
_TRL_HEADER = r"""
if { [catch { set _s $::DboSession_s_pDboSession }] } { return "no Capture Dbo session yet (is Capture fully started?)" }
DboSession -this $_s
set _st [DboState]
set _null NULL
set _out {}
set _diter [$_s NewDesignsIter $_st]
set _d [$_diter NextDesign $_st]
while { $_d != $_null } {
    set _dn [DboTclHelper_sMakeCString]
    catch { $_d GetName $_dn }
    set _dname [DboTclHelper_sGetConstCharPtr $_dn]
    set _viter [$_d NewViewsIter $_st $::IterDefs_SCHEMATICS]
    set _v [$_viter NextView $_st]
    while { $_v != $_null } {
        set _sch [DboViewToDboSchematic $_v]
        if { $_sch != $_null } {
            set _sn [DboTclHelper_sMakeCString]
            catch { $_sch GetName $_sn }
            set _sname [DboTclHelper_sGetConstCharPtr $_sn]
            set _piter [$_sch NewPagesIter $_st]
            set _p [$_piter NextPage $_st]
            while { $_p != $_null } {
                set _pn [DboTclHelper_sMakeCString]
                catch { $_p GetName $_pn }
                set _pname [DboTclHelper_sGetConstCharPtr $_pn]
                %PAGE_BODY%
                set _p [$_piter NextPage $_st]
            }
            catch { delete_DboSchematicPagesIter $_piter }
        }
        set _v [$_viter NextView $_st]
    }
    catch { delete_DboLibViewsIter $_viter }
    set _d [$_diter NextDesign $_st]
}
catch { delete_DboSessionDesignsIter $_diter }
catch { $_st -delete }
if { [llength $_out] == 0 } { return "nothing found" }
join $_out "\n"
"""


def _traversal(page_body: str) -> str:
    return _TRL_HEADER.replace("%PAGE_BODY%", page_body)


# --------------------------------------------------------------------------
# layer 4: COM fallback (bootstrap before the agent exists)
# --------------------------------------------------------------------------

@mcp.tool()
def com_launch_capture() -> str:
    """通过 COM 启动 OrCAD Capture。

    Capture 启动时会自动加载 capAutoLoad 里的 MCP agent 并连接 bridge,
    之后所有 TCL 工具即可使用。返回启动状态。
    """
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    try:
        app = win32com.client.Dispatch("Capture.Application")
        _ = app  # touch to force server start
        return "Capture launched via COM (agent will connect to the bridge within ~5s)."
    finally:
        pythoncom.CoUninitialize()


@mcp.tool()
def com_quit_capture() -> str:
    """通过 COM 关闭正在运行的 OrCAD Capture(未保存的设计可能弹提示)。"""
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    try:
        try:
            app = win32com.client.GetActiveObject("Capture.Application")
        except Exception:
            app = win32com.client.Dispatch("Capture.Application")
        app.Quit()
        return "Quit() sent to Capture."
    finally:
        pythoncom.CoUninitialize()


# --------------------------------------------------------------------------
# layer 1: status & high-level design tools
# --------------------------------------------------------------------------

@mcp.tool()
def capture_status() -> str:
    """查看 MCP bridge 状态:有哪些 Capture 实例已连接、当前活动设计是什么。"""
    br.BRIDGE.ensure()
    sessions = br.BRIDGE.all_sessions()
    if not sessions:
        return ("bridge listening on 127.0.0.1:%d; no Capture agent connected.\n"
                "Use com_launch_capture, or start Capture manually (agent must be "
                "installed in capAutoLoad)." % br.BRIDGE.port)
    lines = [f"bridge listening on 127.0.0.1:{br.BRIDGE.port}, "
             f"{len(sessions)} agent session(s):"]
    for s in sessions:
        try:
            design = _cap(_ACTIVE_DESIGN, timeout=20)
        except Exception as e:
            design = f"<eval failed: {e}>"
        lines.append(f"  pid={s.info.get('pid', '?')} tcl={s.info.get('tcl', '?')} "
                     f"active_design={design}")
    return "\n".join(lines)


@mcp.tool()
def bridge_diagnostics() -> str:
    """诊断 MCP 桥接:bridge 监听状态、已连接会话、PING 往返延迟。"""
    br.BRIDGE.ensure()
    sessions = br.BRIDGE.all_sessions()
    if not sessions:
        return f"bridge on 127.0.0.1:{br.BRIDGE.port}: NO agent connected"
    rows = []
    for s in sessions:
        t0 = time.time()
        ok = s.ping()
        dt = (time.time() - t0) * 1000
        rows.append(f"pid={s.info.get('pid', '?')} ping={'OK' if ok else 'FAIL'} ({dt:.0f} ms)")
    return f"bridge on 127.0.0.1:{br.BRIDGE.port}:\n" + "\n".join(rows)


# --------------------------------------------------------------------------
# layer 2: the escape hatch
# --------------------------------------------------------------------------

@mcp.tool()
def tcl_eval(code: str, session_pid: int | None = None, timeout_s: float = DEFAULT_TIMEOUT) -> str:
    """在 OrCAD Capture 进程内执行任意 TCL 脚本并返回结果。

    这是万能工具:全部 Dbo 数据库 API(用 tcl_api_search 或 docs/appendixB 查)、
    用户操作命令(Menu、GetSelectedObjects、GetActivePage 等,见 appendixA)
    都可调用。脚本在全局作用域执行,多条语句返回最后一条的值。
    注意:会弹出对话框的命令(如 Menu 打开设置窗)会阻塞直到对话框关闭。
    """
    return _clip(_cap(code, timeout=timeout_s, pid=session_pid))


# --------------------------------------------------------------------------
# layer 3: API reference search
# --------------------------------------------------------------------------

@mcp.tool()
def tcl_api_search(query: str, limit: int = 30) -> str:
    """在提取的官方《OrCAD Capture Tcl/Tk Extensions》手册中检索命令。

    query 为大小写不敏感的子串。覆盖:
      Appendix A  用户操作命令(Menu/OpenDesign/GetSelectedObjects...)
      Appendix B  Dbo 数据库类与方法(数据库 API 全集)
      Appendix C  CIS 命令
      章节摘录    自动加载/遍历/属性/PDF导出/通信服务器
    返回 文件:行号:内容。找到命令名后,用 tcl_eval 直接试验。
    """
    files = [
        ("appendixA_user_commands", "appendixA_capture_commands.txt"),
        ("appendixB_dbo_database", "appendixB_database_commands.txt"),
        ("appendixC_cis", "appendixC_cis_commands.txt"),
        ("sec_autoload", "sec_autoload_p13-16.txt"),
        ("sec_dbapi_walkthrough", "sec_dbapi_p29-42.txt"),
        ("sec_commserver", "sec_commserver_p102-105.txt"),
        ("sec_pdfexport", "sec_pdfexport_p86-99.txt"),
    ]
    pat = re.compile(re.escape(query), re.IGNORECASE)
    out: list[str] = []
    for label, fname in files:
        path = os.path.join(DOCS_DIR, fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if pat.search(line):
                    out.append(f"{label}:{i}: {line.strip()}")
                    if len(out) >= max(1, limit):
                        return "\n".join(out)
    return "\n".join(out) if out else f"no match for {query!r}"


# --------------------------------------------------------------------------
# high-level design tools
# --------------------------------------------------------------------------

_DESIGNS_ONLY = r"""
if { [catch { set _s $::DboSession_s_pDboSession }] } { return "no Capture Dbo session yet (is Capture fully started?)" }
DboSession -this $_s
set _st [DboState]
set _null NULL
set _out {}
set _diter [$_s NewDesignsIter $_st]
set _d [$_diter NextDesign $_st]
while { $_d != $_null } {
    set _dn [DboTclHelper_sMakeCString]
    catch { $_d GetName $_dn }
    lappend _out [DboTclHelper_sGetConstCharPtr $_dn]
    set _d [$_diter NextDesign $_st]
}
catch { delete_DboSessionDesignsIter $_diter }
catch { $_st -delete }
if { [llength $_out] == 0 } { return "no designs open" }
join $_out "\n"
"""


@mcp.tool()
def list_designs() -> str:
    """列出 Capture 会话中打开的所有设计(.dsn)。"""
    return _clip(_cap(_DESIGNS_ONLY))


@mcp.tool()
def list_pages() -> str:
    """列出所有打开设计的页结构:design | schematic | page。"""
    return _clip(_cap(_traversal(
        'lappend _out "$_dname | $_sname | $_pname"\n')))


@mcp.tool()
def list_parts(schematic: str = "", page: str = "") -> str:
    """列出所有元件实例:REFDES | VALUE | SOURCE_LIB | SCHEMATIC | PAGE | X | Y。

    schematic/page 为可选的大小写不敏感子串过滤(留空=不过滤)。
    """
    body = r"""
    if { [string match -nocase $fsch_pat $_sname] && [string match -nocase $fpage_pat $_pname] } {
        set _iiter [$_p NewPartInstsIter $_st]
        set _inst [$_iiter NextPartInst $_st]
        while { $_inst != $_null } {
            set _pl [DboPartInstToDboPlacedInst $_inst]
            if { $_pl != $_null } {
                set _ref [DboTclHelper_sMakeCString]
                set _val [DboTclHelper_sMakeCString]
                set _lib [DboTclHelper_sMakeCString]
                catch { $_pl GetReference $_ref }
                catch { $_pl GetPartValue $_val }
                catch { $_pl GetSourceLibName $_lib }
                set _x "?"
                set _y "?"
                if { ![catch { set _loc [$_pl GetLocation $_st] }] } {
                    catch { set _x [DboTclHelper_sGetCPointX $_loc] }
                    catch { set _y [DboTclHelper_sGetCPointY $_loc] }
                }
                lappend _out "[DboTclHelper_sGetConstCharPtr $_ref] | [DboTclHelper_sGetConstCharPtr $_val] | [DboTclHelper_sGetConstCharPtr $_lib] | $_sname | $_pname | $_x | $_y"
            }
            set _inst [$_iiter NextPartInst $_st]
        }
        catch { delete_DboPagePartInstsIter $_iiter }
    }
    """
    code = ("set fsch_pat " + tcl_quote(f"*{schematic}*") + "\n"
            + "set fpage_pat " + tcl_quote(f"*{page}*") + "\n"
            + _traversal(body))
    return _clip(_cap(code))


@mcp.tool()
def get_part_properties(refdes: str) -> str:
    """按位号(REFDES,如 U1)查找元件并列出其全部有效属性(名称=值)。"""
    body = r"""
    if { $found == 0 } {
        set _iiter [$_p NewPartInstsIter $_st]
        set _inst [$_iiter NextPartInst $_st]
        while { $_inst != $_null } {
            set _pl [DboPartInstToDboPlacedInst $_inst]
            if { $_pl != $_null } {
                set _ref [DboTclHelper_sMakeCString]
                catch { $_pl GetReference $_ref }
                if { [string equal -nocase [DboTclHelper_sGetConstCharPtr $_ref] $target] } {
                    set found 1
                    lappend _out "design=$_dname schematic=$_sname page=$_pname"
                    set _epiter [$_pl NewEffectivePropsIter $_st]
                    set _en [DboTclHelper_sMakeCString]
                    set _ev [DboTclHelper_sMakeCString]
                    set _et [DboTclHelper_sMakeDboValueType]
                    set _ee [DboTclHelper_sMakeInt]
                    set _ps [$_epiter NextEffectiveProp $_en $_ev $_et $_ee]
                    while { [$_ps OK] == 1 } {
                        lappend _out "[DboTclHelper_sGetConstCharPtr $_en]=[DboTclHelper_sGetConstCharPtr $_ev]"
                        set _ps [$_epiter NextEffectiveProp $_en $_ev $_et $_ee]
                    }
                    catch { delete_DboEffectivePropsIter $_epiter }
                }
            }
            set _inst [$_iiter NextPartInst $_st]
        }
        catch { delete_DboPagePartInstsIter $_iiter }
    }
    """
    code = ("set target " + tcl_quote(refdes) + "\nset found 0\n" + _traversal(body)
            + "\nif { $found == 0 } { return " + tcl_quote(f"part not found: {refdes}") + " }"
            + '\njoin $_out "\\n"')
    return _clip(_cap(code))


@mcp.tool()
def set_part_property(refdes: str, prop_name: str, value: str) -> str:
    """按位号设置元件属性(等效属性写入,如 VALUE / PCB Footprint / Voltage 等)。"""
    body = r"""
    if { $found == 0 } {
        set _iiter [$_p NewPartInstsIter $_st]
        set _inst [$_iiter NextPartInst $_st]
        while { $_inst != $_null } {
            set _pl [DboPartInstToDboPlacedInst $_inst]
            if { $_pl != $_null } {
                set _ref [DboTclHelper_sMakeCString]
                catch { $_pl GetReference $_ref }
                if { [string equal -nocase [DboTclHelper_sGetConstCharPtr $_ref] $target] } {
                    set found 1
                    set _pnc [DboTclHelper_sMakeCString $pname]
                    set _pvc [DboTclHelper_sMakeCString $pval]
                    set _sst [$_pl SetEffectivePropStringValue $_pnc $_pvc]
                    if { [$_sst OK] == 1 } {
                        lappend _out "OK: $target $pname=$pval (design=$_dname schematic=$_sname page=$_pname)"
                    } else {
                        lappend _out "FAILED: $target $pname=$pval"
                    }
                }
            }
            set _inst [$_iiter NextPartInst $_st]
        }
        catch { delete_DboPagePartInstsIter $_iiter }
    }
    """
    code = ("set target " + tcl_quote(refdes) + "\n"
            + "set pname " + tcl_quote(prop_name) + "\n"
            + "set pval " + tcl_quote(value) + "\n"
            + "set found 0\n" + _traversal(body)
            + "\nif { $found == 0 } { return " + tcl_quote(f"part not found: {refdes}") + " }"
            + '\njoin $_out "\\n"')
    return _cap(code)


@mcp.tool()
def open_design(dsn_path: str) -> str:
    """在 Capture 会话中打开一个 .dsn 设计(绝对路径)。"""
    code = r"""
if { [catch { set _s $::DboSession_s_pDboSession }] } { return "no Capture Dbo session yet (is Capture fully started?)" }
DboSession -this $_s
set _st [DboState]
set _p [DboTclHelper_sMakeCString %PATH%]
set _d [$_s GetDesignAndSchematics $_p $_st]
if { $_d == "NULL" } { error "open failed: %QPATH%" }
set _n [DboTclHelper_sMakeCString]
catch { $_d GetName $_n }
return "opened: [DboTclHelper_sGetConstCharPtr $_n]"
""".replace("%PATH%", tcl_quote(dsn_path)).replace("%QPATH%", dsn_path)
    return _cap(code, timeout=300.0)


@mcp.tool()
def save_design() -> str:
    """保存当前活动设计(相当于 File>Save;另存请用 tcl_eval + SaveDesignAs)。"""
    code = r"""
if { [catch { set _s $::DboSession_s_pDboSession }] } { return "no Capture Dbo session yet (is Capture fully started?)" }
DboSession -this $_s
set _d [$_s GetActiveDesign]
if { $_d == "NULL" } { error "no active design" }
set _st [$_s SaveDesign $_d]
if { [catch { $_st OK } ok] } { return "save command issued (no status object returned)" }
if { $ok == 1 } { return "design saved" } else { return "save FAILED" }
"""
    return _cap(code, timeout=300.0)


@mcp.tool()
def run_menu(menu_path: str) -> str:
    """触发 Capture 菜单命令,如 Tools::Annotate、View::Zoom::Redraw、File::Save。

    菜单路径用 :: 分隔(与 TCL 日志写法一致)。会弹对话框的菜单会阻塞到对话框关闭。
    提示:在 Capture Command Window 执行 SetOptionBool Journaling TRUE 后,
    任何 UI 操作对应的 TCL 命令都会记录到 %TEMP%\\CAPTURELOG\\OrCaptureLogFile.captcl,
    可据此找到某项 UI 操作对应的菜单命令,再用本工具或 tcl_eval 复现。
    """
    return _cap("Menu %s" % tcl_quote(menu_path))


if __name__ == "__main__":
    br.BRIDGE.ensure()
    mcp.run()
