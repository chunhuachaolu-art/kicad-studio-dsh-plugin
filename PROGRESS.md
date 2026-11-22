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

## 2026-11-23 冒烟结果（全过，零 LLM）

- venv：fastmcp 4.2.4 + pydantic + numpy 装机成功；`kicad-studio-server.exe` 入口生成。
- tools/list：**25 工具**全量注册（pcb_* 7 + kicad_* 18），快照 `out/smoke/tools_list.json` sha256 前 16 位 `d6589117a10ec746`。
- `pcb_spec_example`：ne555_blinker spec 落盘工作区 ✓
- `kicad_check_spec_file`：走 `F:\kicad` 真实符号库校验，0 错误 0 警告，引脚表真实返回 ✓（Windows 路径补丁实测生效）
- `pcb_build` 真板全流程：**DRC 0 错误 / 0 警告 / 0 未连通**（KiCad 10.0.5），板 `ne555_blinker.kicad_pcb` ✓
- `pcb_render` ✓；`kicad_checks` drc.passed=true ✓；`pcb_export_fab` 产出 gerber_zip + kicad_project.zip + bom.csv + pos.csv ✓
- dsh 本地安装：`dsh plugin --profile studio-test add <本仓库>` 成功（pnpm link），`dsh --profile studio-test --dump-config` 可见本插件 bundle 层与 mcp-kicad MCP 块 ✓（scratch profile，未动用户 web profile）

## 待办 / 门

- [x] venv 依赖安装完成（fastmcp/pydantic/numpy）。
- [x] 冒烟通过：tools/list 快照 + sha256、spec example、库校验真实输出。
- [x] pcb_build 真板冒烟：建板→DRC→渲染→checks→fab 导出全过。
- [x] dsh 本地安装验证（scratch profile studio-test + --dump-config 可见）。
- [ ] 用户侧 dsh 全链路对话测试（需模型 key，用户自做，参照 bridge 先例）。
- [x] GitHub 推送（2026-11-23 用户令"1做一下"）：`github.com/chunhuachaolu-art/kicad-studio-dsh-plugin` public，main 已推（55c0269+518a00f）。
- [x] npm publish（2026-11-23）：`kicad-studio-dsh-plugin@0.1.0` 已上线（registry 实测 version/latest=0.1.0）。过程要点：账号 zdqrbq 为当日新注册、npm 强制 2FA（auth-and-writes）；用户 2FA 是安全钥匙（passkey），CLI 无法 OTP → 走 granular token + Bypass 2FA；第一个 token 没勾豁免（EOTP/404）、第二个 token 首次复制无效（E401）、重配后发布成功。`.npmrc` 现存有效 token 由用户自配。
- [ ] token 卫生：第一个 7 天 token（已在对话中出现过）建议 revoke 或等其自然过期；当前 .npmrc 里的 token 可留作后续发版。
- [ ] 插件市场上架 / awesome PR = 另行用户门。
- [ ] 插件市场上架 / awesome PR = 另行用户门。
- [ ] 可选：把 skills/kicad-board/SKILL.md 改写为 dsh 侧 agent 指南（dsh 插件暂无 skill 挂载位，先以 README 工具流程代替）。
