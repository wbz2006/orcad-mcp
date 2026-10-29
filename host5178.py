# -*- coding: utf-8 -*-
"""Persistent bridge host: 5178 = TCL agent (Capture), 5179 = script clients.

Clients send one line: "EVAL <code-with-newlines-as-\x01>" and get back
"OK <res>" or "ERR <res>". This lets many short-lived scripts drive Capture
while the agent keeps ONE stable, long-lived connection (sudden listener
death mid-session is suspected of crashing Capture's TCL layer).
"""
import sys, os, socket, threading, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\Main_FIles\free-deng\orcad-mcp")
os.environ.setdefault("ORCAD_MCP_PORT", "5178")
import bridge as br

br.BRIDGE.ensure()
print("[host] agent bridge up on 5178", flush=True)

cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cli.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
cli.bind(("127.0.0.1", 5179))
cli.listen(8)
print("[host] client bridge up on 5179", flush=True)

def client_loop(conn):
    try:
        f = conn.makefile("r", encoding="utf-8", newline="\n")
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                if line.startswith("EVAL "):
                    code = line[5:].replace("\x01", "\n")
                    s = br.BRIDGE.session()
                    res = s.eval(code, timeout=120.0)
                    conn.sendall(("OK " + res.replace("\n", "\x01") + "\n").encode("utf-8"))
                elif line.startswith("PING"):
                    conn.sendall(b"OK PONG\n")
                else:
                    conn.sendall(b"ERR unknown command\n")
            except Exception as e:
                try:
                    conn.sendall(("ERR " + str(e).replace("\n", " ") + "\n").encode("utf-8"))
                except OSError:
                    break
    except OSError:
        pass
    finally:
        try: conn.close()
        except OSError: pass

def accept_clients():
    while True:
        try:
            conn, _ = cli.accept()
        except OSError:
            return
        conn.settimeout(None)
        threading.Thread(target=client_loop, args=(conn,), daemon=True).start()

threading.Thread(target=accept_clients, daemon=True).start()
print("[host] ready", flush=True)
time.sleep(7200)
