"""Protocol smoke test: a fake TCL agent validates the bridge end-to-end.

模拟 agent 行为:连上 bridge → HELLO → 收 EVAL 就(假)执行 → 回 OK/ERR。
验证:正常求值、多行脚本(\\x01 转义)、TCL 错误回传、结果换行还原。
"""

import socket
import sys
import threading
import time

sys.path.insert(0, ".")
import bridge as br  # noqa: E402

PORT = 5188  # 避开默认端口,防冲突


def fake_agent(results: dict, received: list):
    s = socket.create_connection(("127.0.0.1", PORT), timeout=10)
    f = s.makefile("r", encoding="utf-8", newline="\n")
    s.sendall(b"HELLO pid=424242 tcl=8.4.20 exe=fake-capture\n")
    for line in f:
        line = line.rstrip("\n")
        received.append(line)
        if line.startswith("EVAL "):
            code = line[5:].replace("\x01", "\n")
            if code in results:
                ok, res = results[code]
                payload = res.replace("\n", "\x01")
                s.sendall(f"{'OK' if ok else 'ERR'} {payload}\n".encode())
            else:
                s.sendall(f"OK code-ok\n".encode())
        elif line == "PING":
            s.sendall(b"PONG\n")
    s.close()


def main() -> int:
    b = br.Bridge(port=PORT)
    b.start()
    received: list = []
    results = {
        "expr 1+1": (True, "2"),
        "line one\nline two": (True, "result A\nresult B"),
        "error boom": (False, "invalid command name \"boom\""),
    }
    t = threading.Thread(target=fake_agent, args=(results, received), daemon=True)
    t.start()

    # 等 agent 连上
    for _ in range(50):
        if b.all_sessions():
            break
        time.sleep(0.1)
    assert b.all_sessions(), "fake agent did not connect"

    sess = b.session()
    checks = []
    r = sess.eval("expr 1+1")
    checks.append(("simple eval", r == "2"))
    r = sess.eval("line one\nline two")
    checks.append(("multiline escape roundtrip", r == "result A\nresult B"))
    try:
        sess.eval("error boom")
        checks.append(("tcl error propagates", False))
    except RuntimeError as e:
        checks.append(("tcl error propagates", "boom" in str(e)))
    checks.append(("ping", sess.ping()))
    checks.append(("hello info", sess.info.get("pid") == "424242"))

    ok = True
    for name, passed in checks:
        print(("PASS" if passed else "FAIL"), name)
        ok = ok and passed
    print("received by fake agent:", received)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
