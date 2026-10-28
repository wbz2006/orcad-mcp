"""TCP bridge between the ZCode MCP server and the TCL agent inside OrCAD Capture.

Protocol (line-based UTF-8, newlines escaped as \\x01):
    agent -> bridge : "HELLO pid=<pid> tcl=<ver> exe=<path>" | "OK <res>" | "ERR <res>" | "PONG"
    bridge -> agent : "EVAL <code>" | "PING" | "QUITAGENT"

Standalone run (for manual testing, agent connects to it):
    python bridge.py --port 5177 --stay
"""

from __future__ import annotations

import argparse
import os
import sys
import socket
import threading
import time

DEFAULT_PORT = int(os.environ.get("ORCAD_MCP_PORT", "5177"))


class AgentSession:
    """One connected Capture instance (one agent socket)."""

    def __init__(self, conn: socket.socket, addr, bridge: "Bridge"):
        self.conn = conn
        self.addr = addr
        self.bridge = bridge
        self.info: dict[str, str] = {}
        self.alive = True
        self.connected_at = time.time()
        self._send_lock = threading.Lock()
        self._eval_lock = threading.Lock()
        self._event = threading.Event()
        self._reply: tuple[bool, str] | None = None
        self._hello_done = threading.Event()
        threading.Thread(target=self._reader, daemon=True).start()

    # ---- low level -------------------------------------------------------

    def _send(self, line: str) -> None:
        with self._send_lock:
            self.conn.sendall((line + "\n").encode("utf-8"))

    def _resolve(self, ok: bool, payload: str) -> None:
        self._reply = (ok, payload.replace("\x01", "\n"))
        self._event.set()

    def _wait_hello(self, timeout: float = 10.0) -> bool:
        self._hello_done.wait(timeout)
        return self._hello_done.is_set()

    # ---- reader ----------------------------------------------------------

    def _reader(self) -> None:
        try:
            f = self.conn.makefile("r", encoding="utf-8", newline="\n")
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                if line.startswith("HELLO"):
                    for kv in line.split()[1:]:
                        if "=" in kv:
                            k, _, v = kv.partition("=")
                            self.info[k] = v.replace("\x01", " ")
                    self._hello_done.set()
                    print(f"[bridge] agent connected pid={self.info.get('pid', '?')} "
                          f"tcl={self.info.get('tcl', '?')}", file=sys.stderr)
                elif line.startswith("OK "):
                    self._resolve(True, line[3:])
                elif line.startswith("ERR "):
                    self._resolve(False, line[4:])
                elif line.strip() == "PONG":
                    self._resolve(True, "PONG")
        except (ConnectionError, OSError):
            pass
        finally:
            self.alive = False
            self._hello_done.set()
            self._event.set()  # wake up any pending eval
            self.bridge._remove(self)
            print("[bridge] agent disconnected", file=sys.stderr)

    # ---- public API ------------------------------------------------------

    def eval(self, code: str, timeout: float = 60.0) -> str:
        """Run a TCL script inside Capture, return its result. Raises on TCL error."""
        with self._eval_lock:
            if not self.alive:
                raise RuntimeError("agent disconnected (is Capture running with the agent loaded?)")
            self._event.clear()
            self._reply = None
            payload = code.replace("\r", "").replace("\n", "\x01")
            self._send(f"EVAL {payload}")
            if not self._event.wait(timeout):
                self.alive = False
                raise TimeoutError(f"TCL eval timed out after {timeout}s")
            if not self.alive:
                raise RuntimeError("agent disconnected while evaluating")
            assert self._reply is not None
            ok, res = self._reply
            if ok:
                return res
            raise RuntimeError(f"TCL error: {res}")

    def ping(self, timeout: float = 8.0) -> bool:
        try:
            with self._eval_lock:
                if not self.alive:
                    return False
                self._event.clear()
                self._reply = None
                self._send("PING")
                return self._event.wait(timeout) and self.alive
        except (ConnectionError, OSError, RuntimeError):
            return False


class Bridge:
    """Accepts agent connections on 127.0.0.1:<port> and dispatches commands."""

    def __init__(self, port: int = DEFAULT_PORT):
        self.port = port
        self.sessions: dict[int, AgentSession] = {}  # pid -> session
        self._lock = threading.Lock()
        self._started = False
        self._listen_sock: socket.socket | None = None

    # ---- lifecycle -------------------------------------------------------

    def start(self) -> None:
        if self._started:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Windows: exclusive bind so a second Bridge (e.g. MCP server vs a
        # leftover test process) cannot silently share the port.
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            sock.bind(("127.0.0.1", self.port))
        except OSError as e:
            raise RuntimeError(
                f"cannot bind 127.0.0.1:{self.port} ({e}). "
                "Is another bridge running? Set ORCAD_MCP_PORT to change the port."
            ) from e
        sock.listen(4)
        self._listen_sock = sock
        self._started = True
        threading.Thread(target=self._accept_loop, args=(sock,), daemon=True).start()
        print(f"[bridge] listening on 127.0.0.1:{self.port}", file=sys.stderr)

    def stop(self) -> None:
        if self._listen_sock:
            try:
                self._listen_sock.close()
            except OSError:
                pass
        self._started = False

    # ---- internals -------------------------------------------------------

    def _accept_loop(self, sock: socket.socket) -> None:
        while True:
            try:
                conn, addr = sock.accept()
            except OSError:
                return
            conn.settimeout(60.0)
            session = AgentSession(conn, addr, self)
            if not session._wait_hello(60.0):
                session.alive = False
                try:
                    conn.close()
                except OSError:
                    pass
                continue
            conn.settimeout(None)
            pid_raw = session.info.get("pid", "0")
            try:
                pid = int(pid_raw)
            except ValueError:
                pid = id(session)
            with self._lock:
                self.sessions[pid] = session

    def _remove(self, session: AgentSession) -> None:
        with self._lock:
            for pid, s in list(self.sessions.items()):
                if s is session:
                    self.sessions.pop(pid, None)

    # ---- public API ------------------------------------------------------

    def ensure(self) -> None:
        if not self._started:
            self.start()

    def session(self, pid: int | None = None) -> AgentSession:
        """Pick a live session: by pid, else the newest alive one."""
        self.ensure()
        with self._lock:
            sessions = list(self.sessions.items())
        if pid is not None:
            s = self.sessions.get(pid)
            if s and s.alive:
                return s
            raise RuntimeError(f"no live agent session with pid {pid}")
        alive = [(p, s) for p, s in sessions if s.alive]
        if not alive:
            raise RuntimeError(
                "no Capture agent connected. Start OrCAD Capture (with the agent "
                "installed in capAutoLoad) — it will connect automatically."
            )
        alive.sort(key=lambda ps: ps[1].connected_at, reverse=True)
        return alive[0][1]

    def all_sessions(self) -> list[AgentSession]:
        with self._lock:
            return [s for s in self.sessions.values() if s.alive]


BRIDGE = Bridge()


def main() -> None:
    ap = argparse.ArgumentParser(description="OrCAD Capture MCP TCP bridge")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--stay", action="store_true", help="keep running (default: run until Ctrl-C)")
    args = ap.parse_args()
    b = Bridge(port=args.port)
    b.start()
    print("[bridge] waiting for Capture agent... (Ctrl-C to exit)", file=sys.stderr)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("[bridge] bye", file=sys.stderr)


if __name__ == "__main__":
    main()
