"""No-model smoke test: spawn the MCP server exactly like dsh would (entry-point exe on PATH
of the repo venv), do initialize + tools/list, then call the two KiCad-free bootstrap tools.
Results land in out/smoke/. Zero LLM calls.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "venv" / "Scripts" / "kicad-studio-server.exe"
OUT = ROOT / "out" / "smoke"
OUT.mkdir(parents=True, exist_ok=True)

ENV = os.environ | {
    "PYTHONUTF8": "1",
    "PYTHONIOENCODING": "utf-8",
    "ZCODE_KICAD_APP": r"F:\kicad",
    "ZCODE_WORKSPACE_ROOT": str(OUT / "ws"),
    "ZCODE_PLUGIN_DATA": str(OUT / "data"),
}
for d in ("ws", "data"):
    (OUT / d).mkdir(parents=True, exist_ok=True)

log = open(OUT / "server_stderr.log", "w", encoding="utf-8")
p = subprocess.Popen([str(EXE)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log,
                     env=ENV, text=True, encoding="utf-8", cwd=str(OUT / "ws"))
_id = 0


def send(obj):
    p.stdin.write(json.dumps(obj) + "\n")
    p.stdin.flush()


def recv():
    line = p.stdout.readline()
    if not line:
        raise RuntimeError("server closed stdout; see server_stderr.log")
    return json.loads(line)


def call(method, params=None):
    global _id
    _id += 1
    send({"jsonrpc": "2.0", "id": _id, "method": method, "params": params or {}})
    return recv()


init = call("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                           "clientInfo": {"name": "studio-smoke", "version": "0.1.0"}})
print("INIT_SERVER:", init["result"]["serverInfo"]["name"], init["result"]["serverInfo"].get("version", ""))
send({"jsonrpc": "2.0", "method": "notifications/initialized"})

r = call("tools/list")
tools = r["result"]["tools"]
names = [t["name"] for t in tools]
print("TOOLCOUNT:", len(tools))
print("TOOLS:", json.dumps(names))
(OUT / "tools_list.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")

# KiCad-free bootstrap calls: example spec, then library check of that spec (exercises the
# Windows kicad-cli/library path resolution patched into kicad/paths.py).
spec_path = OUT / "ws" / "kicad" / "ne555_blinker_spec.json"
r1 = call("tools/call", {"name": "pcb_spec_example", "arguments": {}})
print("SPEC_EXAMPLE:", json.dumps(r1["result"].get("structuredContent", r1["result"]), ensure_ascii=False)[:400])
(OUT / "spec_example.json").write_text(json.dumps(r1, ensure_ascii=False, indent=1), encoding="utf-8")

if spec_path.is_file():
    r2 = call("tools/call", {"name": "kicad_check_spec_file", "arguments": {"spec_path": str(spec_path)}})
    sc = r2["result"].get("structuredContent", {})
    print("CHECK_SPEC:", json.dumps(sc, ensure_ascii=False)[:600])
    (OUT / "check_spec.json").write_text(json.dumps(r2, ensure_ascii=False, indent=1), encoding="utf-8")
else:
    print("CHECK_SPEC: skipped (no spec file written by pcb_spec_example)")

p.terminate()
print("SMOKE_OK")
