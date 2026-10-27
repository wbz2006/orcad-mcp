#///////////////////////////////////////////////////////////////////////////////
# orcad_mcp_agent.tcl — MCP bridge agent for OrCAD Capture 16.6 (Tcl 8.4)
#
# 放置于 <CDSROOT>\tools\capture\tclscripts\capAutoLoad\ 后随 Capture 启动自动加载。
# 它通过 TCP 连接外部 Python bridge (默认 127.0.0.1:5177)，把收到的 TCL 脚本
# 在 Capture 进程内 uplevel 执行并回传结果 —— 这是 AI 直接操作 Capture 的通道。
#
# 协议（行文本 UTF-8，换行以 \x01 转义）:
#   agent -> bridge : "HELLO pid=<pid> tcl=<ver> exe=<path>" | "OK <res>" | "ERR <res>" | "PONG"
#   bridge -> agent : "EVAL <code>" | "PING" | "QUITAGENT"
#
# 停用方式: 设置环境变量 ORCAD_MCP_DISABLE=1，
#           或在 Capture Command Window 执行 ::orcadmcp::stop
#///////////////////////////////////////////////////////////////////////////////

package require Tcl 8.4

namespace eval ::orcadmcp {
    variable sock       ""
    variable host       "127.0.0.1"
    variable port       5177
    variable enabled    1
    variable started    0
}

if { [info exists ::env(ORCAD_MCP_PORT)] } {
    set ::orcadmcp::port $::env(ORCAD_MCP_PORT)
}
if { [info exists ::env(ORCAD_MCP_DISABLE)] } {
    set ::orcadmcp::enabled 0
}

proc ::orcadmcp::esc { s } {
    return [string map {\n \x01 \r {} \t { }} $s]
}

proc ::orcadmcp::tryConnect { } {
    variable sock
    variable host
    variable port
    variable enabled
    if { !$enabled } { return }
    if { ![string equal $sock ""] } {
        # 既有连接先探活:写入失败(半开连接)则丢弃重建
        if { [catch { puts $sock "" }] } {
            ::orcadmcp::dropSocket
        } else {
            return
        }
    }
    if { [catch { socket $host $port } s] } {
        return ;# bridge 未运行，由 ensureLoop 稍后重试
    }
    set sock $s
    fconfigure $sock -buffering line -encoding utf-8 -translation lf
    fileevent $sock readable ::orcadmcp::onReadable
    set lExe [info nameofexecutable]
    catch { puts $sock "HELLO pid=[pid] tcl=[info patchlevel] port=$port exe=[::orcadmcp::esc $lExe]" }
    puts "orcad-mcp: agent connected to $host:$port"
}

proc ::orcadmcp::ensureLoop { } {
    variable enabled
    if { !$enabled } { return }
    catch { ::orcadmcp::tryConnect }
    after 4000 ::orcadmcp::ensureLoop
}

proc ::orcadmcp::dropSocket { } {
    variable sock
    catch { fileevent $sock readable {} }
    catch { close $sock }
    set sock ""
}

proc ::orcadmcp::onReadable { } {
    variable sock
    if { [string equal $sock ""] } { return }
    if { [catch {
        if { [eof $sock] } {
            ::orcadmcp::dropSocket
            puts "orcad-mcp: bridge connection lost, will retry"
            return
        }
        set n [gets $sock line]
        if { $n < 0 } {
            ::orcadmcp::dropSocket
            return
        }
        if { $n > 0 } { ::orcadmcp::dispatch $line }
    } err] } {
        catch { puts "orcad-mcp: socket error: $err" }
        ::orcadmcp::dropSocket
    }
}

proc ::orcadmcp::runAtGlobal { code } {
    # proc 边界让脚本顶层的 return 拥有确定的"返回脚本值"语义,
    # 避免 Tcl 8.4 里 uplevel #0 + return 被 catch 误判为错误
    uplevel #0 $code
}

proc ::orcadmcp::dispatch { line } {
    variable sock
    set cmd [string range $line 0 3]
    switch -- $cmd {
        EVAL {
            set payload [string range $line 5 end]
            set code [string map {\x01 \n} $payload]
            if { [catch { ::orcadmcp::runAtGlobal $code } res] } {
                catch { puts $sock "ERR [::orcadmcp::esc $res]" }
            } else {
                catch { puts $sock "OK [::orcadmcp::esc $res]" }
            }
        }
        PING       { catch { puts $sock "PONG" } }
        QUITAGENT  { ::orcadmcp::stop }
        default    { }
    }
}

proc ::orcadmcp::stop { } {
    variable enabled
    variable sock
    set enabled 0
    ::orcadmcp::dropSocket
    puts "orcad-mcp: agent stopped"
}

proc ::orcadmcp::start { } {
    variable enabled
    variable started
    set enabled 1
    if { !$started } {
        set started 1
        ::orcadmcp::ensureLoop
    }
}

# 随加载启动；ensureLoop 每 4 秒尝试连接一次 bridge，未连接时零开销等待
::orcadmcp::start
puts "orcad-mcp: agent loaded (target 127.0.0.1:$::orcadmcp::port, disable with ORCAD_MCP_DISABLE)"
