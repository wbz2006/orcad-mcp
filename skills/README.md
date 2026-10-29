# skills/ — AI 方法论(可复用的技能包)

本目录发布 [`orcad-automate`](orcad-automate/SKILL.md):一套让 AI 直接操作 OrCAD Capture / PSpice
的完整方法论与工具用法。它不是 MCP 代码,而是**给 AI 会话读的说明书**——把踩过的坑固化成
可执行流程,让任意 AI IDE(Claude Code / Cursor / ZCode / OpenCode / WorkBuddy …)接手时
不必从零试错。

## 内容

| 文件 | 说明 |
|---|---|
| `orcad-automate/SKILL.md` | 主文档:连接/画图/改图/仿真/软件自身打印导出/安静模式/故障速查表 |
| `orcad-automate/references/api-notes.md` | API 与坑的详单:Tcl/Dbo 签名、坐标约定、打印对话框自动化、Probe 标注、崩溃恢复等 |

## 安装到本机(让 AI 自动加载)

主流 AI IDE 的 agent skills 目录为 `~/.agents/skills/`(Windows:`C:\Users\<你>\.agents\skills\`):

```bat
xcopy /E /I skills\orcad-automate %USERPROFILE%\.agents\skills\orcad-automate
```

装好后,当对话涉及 OrCAD / Capture / PSpice / 原理图 / EDA 仿真时,AI 会按
`SKILL.md` 的 `description` 自动加载。也可以用 ZCode 等客户端的 skill 加载命令手动调用
(`/orcad-automate`)。

## 关于这份副本

- **仓库里的这份是发布源**;`~/.agents/skills/orcad-automate/` 是运行副本。
- 修改流程:先改仓库 → 提交 → 再同步到 `~/.agents/`(或直接改两处后一起提交),
  避免两份内容漂移。
- 迭代记录见 [`docs/skill-iterations.md`](../docs/skill-iterations.md)(5 轮迭代:任务/新坑/改进)。

## 配套脚本(在仓库根目录)

| 脚本 | 用途 |
|---|---|
| `orcad_quiet.py` | **安静模式**:全程窗口消息驱动,不抢焦点不动鼠标;标注用 pymupdf 叠写到打印出的 PDF |
| `probe_export.py` | 物理点击模式(需前台):Probe 加轨迹/双坐标系/原生标注/打印 |
| `cap_open.py` / `cap_activate.py` / `cap_print.py` | Capture 冷启动、切页、打印 |
| `bridge.py` / `server.py` / `agent/` | MCP 服务器与 TCL agent |
| `tcl/prep_ic_loaded.tcl` | 参数化切换静态工作点档位(Rb1/VAMPL/RL/别名) |
