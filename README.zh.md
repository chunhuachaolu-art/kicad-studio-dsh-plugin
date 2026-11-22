# kicad-studio-dsh-plugin（中文）

[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（dsh）插件：把 **KiCad 10 建板流水线**装进 dsh 会话，暴露为 `mcp__kicad__*` 工具族——Agent 从一份 JSON 电路 spec 出发，用真实 KiCad 符号/封装库检查设计、建双层板、自动布线、跑 DRC、渲染，并导出 Gerber/BOM/CPL/STEP/GLB 制造文件。

MCP 服务器本体是 ZCode 官方 [kicad 插件](https://github.com/fxp) v0.6.1（MIT）的 Python 工作器，vendored 后重打包为 `server/py/`（pip 包名 `kicad-studio-server`）。本仓库新增：dsh 插件壳（Cordis bundle，经 `@deepseek-ai/dsh-mcp-client`）、Windows 的 KiCad 路径解析、CI 式冒烟测试。

## 安装

```bash
# 1. Python 服务器：任意 Python >= 3.11
pip install kicad-studio-server          # 发布到 PyPI 后；或本地：
pip install <本仓库>/server/py           # 会一并装入 fastmcp>=4,<5、pydantic、numpy

# 2. 插件
dsh plugin --profile web add github:chunhuachaolu-art/kicad-studio-dsh-plugin
```

任意 profile（`web`、`tui`、`headless`…）均可用。

## 前提

- [dsh](https://www.npmjs.com/package/@deepseek-ai/dsh) 0.2.1-rc.x（`npm i -g @deepseek-ai/dsh`）
- Python **>= 3.11**，已装 `kicad-studio-server`；可执行文件在 `PATH` 上，或用 `KICAD_STUDIO_CMD` 指向它
- 本机装有 **KiCad 10**。无头工具（建板、DRC、渲染、导出）只经 `kicad-cli` 运行，不需要 GUI。

## 配置（环境变量）

| 变量 | 默认 | 含义 |
|---|---|---|
| `KICAD_STUDIO_CMD` | `kicad-studio-server` | 启动 MCP 服务器的命令（不在 PATH 时给 venv 的 `Scripts\kicad-studio-server.exe` 全路径）。 |
| `ZCODE_KICAD_APP` | `/Applications/KiCad/KiCad.app` | KiCad 安装位置。**Windows：**设为安装根目录，如 `F:\kicad`（从中解析 `bin\kicad-cli.exe`、`bin\python.exe`、`share\kicad`）。 |
| `ZCODE_KICAD_CLI` | 自动探测 | 显式覆盖 `kicad-cli` 路径。 |
| `KICAD_STUDIO_WORKSPACE` | 服务器 cwd | 服务器认定的会话工作区根（`./kicad/` 产物落在这里）。 |
| `KICAD_STUDIO_DATA` | `<workspace>/.kicad-plugin` | 按工作区隔离的产物库与 KiCad 私有配置。 |

示例（Windows，仓库 venv）：

```bash
set KICAD_STUDIO_CMD=E:\ZCodeData\ZCodeProject\dsh-kicad-studio\venv\Scripts\kicad-studio-server.exe
set ZCODE_KICAD_APP=F:\kicad
dsh web
```

## 工具流程（Agent 的动作序列）

1. `pcb_spec_example` — 写入示例电路 spec
2. `kicad_check_spec_file` — 用真实 KiCad 库校验 spec
3. `pcb_build` — 摆件、自动布线、导出 `.kicad_pcb`
4. `pcb_render` / `kicad_checks` — 3D 渲染 + DRC 结论
5. `pcb_export_fab` / `kicad_export_files` — Gerber/BOM/CPL/STEP、GLB、分层 SVG

`kicad_board_view` 返回结构化的板级摘要。（ZCode 插件把它渲染成 MCP Apps 侧栏面板；dsh 0.2.1-rc.2 没有 MCP Apps 宿主，所以在 dsh 里同样的数据以工具输出到达，文件产物落工作区，可随时作为 deliverables 呈现。）

## 与原 ZCode 插件的差异

- 无侧栏 UI（dsh 不承载 MCP Apps 资源）——工具相同，面板数据以 JSON 返回。
- `kicad_open_in_kicad` 仍会把可编辑工程导出到 `./kicad/edit/<名称>/`；但拉起 KiCad GUI 本身是 macOS 专属（`open -a`），其他平台返回 `launched=false` 并附说明。
- 与运行中 PCB 编辑器的实时连接（`kicad_live_*`）是 macOS 专属（KiCad 的 `/tmp/kicad/api.sock`），其他平台报告不可用。
- Windows：`ZCODE_KICAD_APP` 指向安装根目录；`bin/kicad-cli.exe`、`bin/python.exe`、`share/kicad` 从那里解析。

## 常见问题

- **会话里工具缺失** — 见 bridge 插件关于 dsh 版本门槛的排查；本插件钉住 `@deepseek-ai/dsh-mcp-client@0.2.1-rc.2` 以匹配 dsh 0.2.1-rc.x。
- **找不到 `kicad-studio-server`** — `pip install`（Python >= 3.11），或把 `KICAD_STUDIO_CMD` 设为可执行文件绝对路径。
- **报 "kicad-cli not found"** — 设 `ZCODE_KICAD_APP`（Windows：安装根目录如 `F:\kicad`）或 `ZCODE_KICAD_CLI`。
- **首次建板慢** — 工作器经 `kicad-cli` 跑真实的摆件/布线/DRC；大板需要数分钟。

## 致谢与许可

- 设计管线与面板：ZCode kicad 插件，作者 冯小平（fxp），MIT — vendored 并有修改（见 NOTICE）。
- 本插件壳：MIT — 见 [LICENSE](LICENSE)。
