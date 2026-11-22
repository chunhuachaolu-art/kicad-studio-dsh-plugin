# kicad-studio-dsh-plugin

[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (dsh) plugin that puts the **KiCad 10 board-design pipeline** into a dsh session as an MCP tool family (`mcp__kicad__*`): from a JSON circuit spec the agent checks the design against real KiCad symbol/footprint libraries, builds and auto-routes a 2-layer board, runs DRC, renders it, and exports Gerber/BOM/CPL/STEP/GLB fabrication outputs.

The MCP server is the Python worker of the ZCode official [kicad plugin](https://github.com/fxp) v0.6.1 (MIT), vendored and repackaged (`server/py/`, pip package `kicad-studio-server`). This repository adds the dsh plugin shell (Cordis bundle via `@deepseek-ai/dsh-mcp-client`), Windows KiCad-path resolution, and CI-style smoke tests.

## Install

```bash
# 1. Python server: any Python >= 3.11
pip install kicad-studio-server          # once published to PyPI, or:
pip install <this-repo>/server/py        # builds fastmcp>=4,<5, pydantic, numpy in

# 2. Plugin
dsh plugin --profile web add github:chunhuachaolu-art/kicad-studio-dsh-plugin
```

Works with any profile (`web`, `tui`, `headless`, ...).

## Requirements

- [dsh](https://www.npmjs.com/package/@deepseek-ai/dsh) 0.2.1-rc.x (`npm i -g @deepseek-ai/dsh`)
- Python **>= 3.11** with `kicad-studio-server` installed (see above); the executable must be on `PATH` or pointed at via `KICAD_STUDIO_CMD`
- **KiCad 10** installed locally. Headless tools (build, DRC, renders, exports) run through `kicad-cli` only — no GUI needed.

## Configuration (environment variables)

| Variable | Default | Meaning |
|---|---|---|
| `KICAD_STUDIO_CMD` | `kicad-studio-server` | Command that launches the MCP server (full path to a venv's `Scripts/kicad-studio-server.exe` if not on `PATH`). |
| `ZCODE_KICAD_APP` | `/Applications/KiCad/KiCad.app` | KiCad install. **Windows:** set to the install root, e.g. `F:\kicad` (resolves `bin\kicad-cli.exe`, `bin\python.exe`, `share\kicad`). |
| `ZCODE_KICAD_CLI` | auto-detect | Explicit `kicad-cli` path override. |
| `KICAD_STUDIO_WORKSPACE` | server cwd | Workspace root the server treats as the session workspace (`./kicad/` outputs land here). |
| `KICAD_STUDIO_DATA` | `<workspace>/.kicad-plugin` | Per-workspace artifact store and KiCad private config. |

Example (Windows, repo venv):

```bash
set KICAD_STUDIO_CMD=E:\ZCodeData\ZCodeProject\dsh-kicad-studio\venv\Scripts\kicad-studio-server.exe
set ZCODE_KICAD_APP=F:\kicad
dsh web
```

## Tool flow (what the agent does)

1. `pcb_spec_example` — write an example circuit spec
2. `kicad_check_spec_file` — validate the spec against real KiCad libraries
3. `pcb_build` — place parts, auto-route, export the `.kicad_pcb`
4. `pcb_render` / `kicad_checks` — 3D render + DRC verdict
5. `pcb_export_fab` / `kicad_export_files` — Gerber/BOM/CPL/STEP, GLB, layer SVGs

`kicad_board_view` returns a structured board summary. (The ZCode plugin renders this as an MCP Apps side panel; dsh 0.2.1-rc.2 has no MCP Apps host, so in dsh the same data arrives as tool output and any file outputs land in the workspace, ready to be presented as deliverables.)

## Differences vs. the original ZCode plugin

- No side-panel UI (dsh has no MCP Apps resource hosting) — same tools, panel data as JSON.
- `kicad_open_in_kicad` still exports the editable project to `./kicad/edit/<name>/`; launching the KiCad GUI itself is macOS-only (`open -a`) and reports `launched=false` with a note elsewhere.
- The live link to a running PCB Editor (`kicad_live_*`) is macOS-only (KiCad's `/tmp/kicad/api.sock`) and reports unavailable elsewhere.
- Windows: `ZCODE_KICAD_APP` points at the install root; `bin/kicad-cli.exe`, `bin/python.exe` and `share/kicad` are resolved from there.

## Troubleshooting

- **Tools missing in the live session** — see the bridge plugin's notes on dsh version gates; this plugin pins `@deepseek-ai/dsh-mcp-client@0.2.1-rc.2` to match dsh 0.2.1-rc.x.
- **`kicad-studio-server` not found** — `pip install` it (Python >= 3.11), or set `KICAD_STUDIO_CMD` to the absolute executable path.
- **"kicad-cli not found"** — set `ZCODE_KICAD_APP` (Windows: install root like `F:\kicad`) or `ZCODE_KICAD_CLI`.
- **First build is slow** — the worker runs real placement/routing/DRC through `kicad-cli`; large boards take minutes.

## Credits & license

- Design pipeline & panel: ZCode kicad plugin by 冯小平 (fxp), MIT — vendored with modifications (see NOTICE).
- This plugin shell: MIT — see [LICENSE](LICENSE).
