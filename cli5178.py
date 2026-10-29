# -*- coding: utf-8 -*-
"""Tiny client for host5178.py (persistent bridge host).

Usage:
    import cli5178
    cli5178.eval("set x 1")
"""
import socket, time

def _conn(timeout=10.0):
    return socket.create_connection(("127.0.0.1", 5179), timeout=timeout)

def eval(code, tcl_timeout=120.0, conn_timeout=15.0):
    payload = code.replace("\r", "").replace("\n", "\x01")
    s = _conn(max(conn_timeout, tcl_timeout))
    try:
        s.sendall(f"EVAL {payload}\n".encode("utf-8"))
        buf = b""
        t0 = time.time()
        while time.time() - t0 < tcl_timeout + 20:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if b"\n" in buf:
                line = buf.decode("utf-8", errors="replace").strip()
                if line.startswith("OK "):
                    return line[3:].replace("\x01", "\n")
                if line.startswith("ERR "):
                    raise RuntimeError("TCL error: " + line[4:].replace("\x01", "\n"))
                if line == "OK":
                    return ""
        raise TimeoutError(f"no reply in {tcl_timeout}s")
    finally:
        try: s.close()
        except OSError: pass

def wait_agent(seconds=120.0):
    t0 = time.time()
    while time.time() - t0 < seconds:
        try:
            return eval("set x 1", tcl_timeout=10, conn_timeout=5)
        except Exception:
            time.sleep(2)
    raise RuntimeError("agent did not connect in time")
