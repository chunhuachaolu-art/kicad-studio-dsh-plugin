"""Follow-up smoke: render + DRC checks + fab export for the board built by smoke_build.py
(reuses the persisted artifact store; no rebuild)."""
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "venv" / "Scripts" / "kicad-studio-server.exe"
OUT = ROOT / "out" / "smoke"

ENV = os.environ | {
    "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8",
    "ZCODE_KICAD_APP": r"F:\kicad",
    "ZCODE_WORKSPACE_ROOT": str(OUT / "ws"),
    "ZCODE_PLUGIN_DATA": str(OUT / "data"),
}
log = open(OUT / "export_server_stderr.log", "w", encoding="utf-8")
p = subprocess.Popen([str(EXE)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log,
                     env=ENV, text=True, encoding="utf-8", cwd=str(OUT / "ws"))
_id = 0


def send(obj):
    p.stdin.write(json.dumps(obj) + "\n"); p.stdin.flush()


def recv():
    line = p.stdout.readline()
    if not line:
        raise RuntimeError("server closed stdout")
    return json.loads(line)


def call(name, args=None):
    global _id
    _id += 1
    send({"jsonrpc": "2.0", "id": _id, "method": "tools/call", "params": {"name": name, "arguments": args or {}}})
    r = recv()
    if r.get("error"):
        raise RuntimeError(f"{name}: {r['error']}")
    res = r["result"]
    if res.get("isError"):
        raise RuntimeError(f"{name}: {json.dumps(res.get('content'), ensure_ascii=False)[:400]}")
    return res.get("structuredContent") or res


send({"jsonrpc": "2.0", "id": 0, "method": "initialize",
      "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "studio-smoke", "version": "0.1.0"}}})
recv()
send({"jsonrpc": "2.0", "method": "notifications/initialized"})

info = call("kicad_info")
pcbs = [a for a in info.get("artifacts", []) if a.get("kind") == "kicad_pcb"]
pcb_id = pcbs[-1]["artifact_id"]
print("PCB:", pcb_id, pcbs[-1].get("name"))

render = call("pcb_render", {"artifact_id": pcb_id})
(OUT / "build_pcb_render.json").write_text(json.dumps(render, ensure_ascii=False, indent=1), encoding="utf-8")
print("RENDER_OK:", render.get("ok"))

checks = call("kicad_checks", {"artifact_id": pcb_id})
(OUT / "build_kicad_checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=1), encoding="utf-8")
print("CHECKS:", json.dumps({k: checks.get(k) for k in ("ok", "drc_passed", "errors", "warnings", "unconnected")}, ensure_ascii=False))

fab = call("pcb_export_fab", {"artifact_id": pcb_id})
(OUT / "build_pcb_export_fab.json").write_text(json.dumps(fab, ensure_ascii=False, indent=1), encoding="utf-8")
kinds = [f.get("kind") for f in fab.get("files", [])]
print("FAB_OK:", fab.get("ok"), "files:", kinds)
print("EXPORT_SMOKE_OK")
p.terminate()
