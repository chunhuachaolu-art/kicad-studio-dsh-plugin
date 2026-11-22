"""Full-pipeline smoke (no LLM): spec -> check -> pcb_build (place+route+DRC) -> render -> checks -> fab export.
Slow: runs real kicad-cli placement/routing/DRC. Results land in out/smoke/build_*.json.
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

log = open(OUT / "build_server_stderr.log", "w", encoding="utf-8")
p = subprocess.Popen([str(EXE)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log,
                     env=ENV, text=True, encoding="utf-8", cwd=str(OUT / "ws"))
_id = 0


def send(obj):
    p.stdin.write(json.dumps(obj) + "\n")
    p.stdin.flush()


def recv():
    line = p.stdout.readline()
    if not line:
        raise RuntimeError("server closed stdout; see build_server_stderr.log")
    return json.loads(line)


def call(name, args=None):
    global _id
    _id += 1
    send({"jsonrpc": "2.0", "id": _id, "method": "tools/call", "params": {"name": name, "arguments": args or {}}})
    r = recv()
    if r.get("error"):
        raise RuntimeError(f"{name} RPC error: {r['error']}")
    res = r["result"]
    if res.get("isError"):
        raise RuntimeError(f"{name} tool error: {json.dumps(res.get('content'), ensure_ascii=False)[:500]}")
    return res.get("structuredContent") or res


def save(name, obj):
    (OUT / f"build_{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


send({"jsonrpc": "2.0", "id": 0, "method": "initialize",
      "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "studio-smoke", "version": "0.1.0"}}})
recv()
send({"jsonrpc": "2.0", "method": "notifications/initialized"})

spec_path = OUT / "ws" / "kicad" / "ne555_blinker_spec.json"
chk = call("kicad_check_spec_file", {"spec_path": str(spec_path)})
sid = chk.get("spec_artifact_id")
print("SPEC_ARTIFACT:", sid)
assert sid, "no spec_artifact_id from kicad_check_spec_file"

build = call("pcb_build", {"spec_artifact_id": sid})
save("pcb_build", build)
drc = build.get("drc") or {}
print("BUILD_OK:", build.get("ok"), "| DRC errors:", drc.get("errors"), "warnings:", drc.get("warnings"),
      "unconnected:", drc.get("unconnected"), "| pcb_artifact_id:", (build.get("kicad_pcb") or {}).get("artifact_id"))

pcb_id = (build.get("kicad_pcb") or {}).get("artifact_id")
if pcb_id:
    render = call("pcb_render", {"artifact_id": pcb_id})
    save("pcb_render", render)
    print("RENDER:", render.get("ok"), (render.get("png") or {}).get("artifact_id", ""))
    checks = call("kicad_checks", {"artifact_id": pcb_id})
    save("kicad_checks", checks)
    print("CHECKS:", json.dumps({k: checks.get(k) for k in ("ok", "drc_passed", "errors", "warnings", "unconnected")}, ensure_ascii=False))

print("BUILD_SMOKE_OK")
p.terminate()
