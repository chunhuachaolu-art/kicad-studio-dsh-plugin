# PROGRESS — kicad-studio-dsh-plugin（dsh-kicad-studio）

任务：把 ZCode 官方 kicad 插件（v0.6.1）的 Python 建板管线移植为 dsh 插件。上承 2026-10-17 的 kicad-mcp-dsh-plugin（薄桥，只读检查）与 pcb-periph-dsh-plugin（CI CLI）；本插件补"从 spec 生成板"的能力位。

## 2026-11-23

- 调研定案：
  - 官方插件 dist/server.mjs 只是解释器解析 + stdio 转发的薄壳；真正的 MCP 服务器（FastMCP，工具 + `ui://kicad/board.html` 面板资源）全在 `dist/py/kicad_server.py`。
  - dsh 0.2.1-rc.2 全量 grep：无 MCP Apps（`mcp-app`）宿主能力；UI 扩展走 React Slot（dsh-client-ui-renderer）。=> 面板不移植，工具面整体平移；产物以文件 + JSON 呈现（可接 dsh-tool-present）。
  - dsh 插件可直接拉起 Python stdio MCP 服务（multisim 样板先例）。
  - macOS 专属面（open -a GUI 启动、/tmp/kicad/api.sock live link）在原代码里本就优雅降级，无需改动。
- 建仓 `E:\ZCodeData\ZCodeProject\dsh-kicad-studio\`：
  - vendor dist/py → `server/py/src/kicad_studio/`（含 kicad/ 工作器包与 panel.html），重打包为 pip 包 `kicad-studio-server`（入口 `kicad-studio-server = kicad_studio.kicad_server:main`）。
  - 代码修改：① kicad/paths.py 增加 Windows 布局解析（`bin/kicad-cli.exe`、`bin/python.exe`、`share/kicad`）与 `ZCODE_KICAD_CLI` 覆盖；② 绝对导入改相对导入、包重构；③ `PAGE = HERE / "panel.html"`（panel.html 随包分发）。
  - 插件壳：package.json（npm 名 kicad-studio-dsh-plugin，钉 dsh-mcp-client@0.2.1-rc.2）+ cordis.patch.yml（stdio，command=`KICAD_STUDIO_CMD` ?? `kicad-studio-server`，透传 ZCODE_KICAD_APP/ZCODE_KICAD_CLI/KICAD_STUDIO_WORKSPACE/KICAD_STUDIO_DATA，toolCallTimeoutMs=600000，failOnStartupError=false）。
  - 文档：README.md / README.zh.md / LICENSE（MIT）/ NOTICE（fxp 插件 vendored 归属、KiCad GPL、依赖许可）。
  - 冒烟：scripts/smoke_tools.py（零 LLM，stdio JSON-RPC：initialize → tools/list 快照落盘 → pcb_spec_example → kicad_check_spec_file，后者实走 F:\kicad 库解析，验证 Windows 路径补丁）。

## 待办 / 门

- [ ] venv 依赖安装完成（fastmcp/pydantic/numpy；PyPI 直连或代理）。
- [ ] 冒烟通过：tools/list 快照 + sha256、spec example、库校验真实输出。
- [ ] （可选加强）pcb_build 真板冒烟：小板全流程（建板→DRC→导出）。
- [ ] dsh 本地安装验证（`dsh plugin --profile web add <本地路径>` + --dump-config 可见）——零 LLM 面。
- [ ] 发布材料终审、npm/GitHub 发布 = 用户门。
