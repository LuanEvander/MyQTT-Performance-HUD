import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).parent


def _reader(stream, prefix_str):
    for line in iter(stream.readline, ""):
        if line:
            print(f"[{prefix_str}] {line}", end="", flush=True)


def main() -> None:
    base_env = os.environ.copy()
    base_env["PYTHONUNBUFFERED"] = "1"

    cmds = [
        ("broker", ["mosquitto", "-v"]),
        ("overlay", [sys.executable, "-m", "src.overlay"]),
        ("collector", [sys.executable, "-m", "src.collector"]),
    ]

    procs: list[tuple[str, subprocess.Popen]] = []

    for name, cmd in cmds:
        proc_env = {**base_env}
        if name == "overlay":
            proc_env["QT_QPA_PLATFORM"] = "wayland"
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=proc_env,
            cwd=str(ROOT),
        )
        procs.append((name, proc))
        t = threading.Thread(target=_reader, args=(proc.stdout, name), daemon=True)
        t.start()
        if name == "broker":
            time.sleep(0.3)

    def cleanup(*_args):
        for name, proc in procs:
            if proc.poll() is None:
                proc.terminate()
        for _name, proc in procs:
            proc.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    while True:
        for name, proc in procs:
            if proc.poll() is not None:
                print(
                    f"[runner] {name} encerrou (código {proc.returncode}), "
                    "derrubando todos..."
                )
                cleanup()
                return
        time.sleep(0.1)


if __name__ == "__main__":
    main()
