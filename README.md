# orcad-mcp — 让 AI 直接操作 OrCAD Capture / PSpice 的 MCP 接口

**Drive OrCAD Capture CIS (16.x) and PSpice from any AI coding agent via MCP.**

`orcad-mcp` 是一个 MCP(Model Context Protocol)服务器:AI 助手(ZCode/Claude/Cursor 等)
可以直接绘制原理图、修改元件属性、运行 PSpice 仿真、导出结果——全程不需要人碰鼠标键盘。

> 不逆向、不破解、不修改任何 OrCAD 二进制。全部基于 OrCAD **自带**的官方自动化接口:
> 内嵌 Tcl/Tk 解释器(16.3+)+ COM 自动化服务器 + 随产品附带的命令行仿真引擎。

## 工作原理 / Architecture

```
AI Agent ──MCP(stdio)──▶ server.py ──TCP 127.0.0.1:5177──▶ TCL agent(运行在 Capture 进程内)
                            │                                 ├─ Dbo 数据库 API(元件/连线/属性/层级)
                            │                                 └─ 用户操作命令(Menu / Place / Select ...)
                            └─ COM 兜底:拉起 / 关闭 Capture
PSpice 引擎(psp_cmd.exe)←── 命令行 .cir 网表 ──┘(Bias Point / Transient / AC ...)
```

- `agent/orcad_mcp_agent.tcl` 放进 `<OrCAD>\tools\capture\tclscripts\capAutoLoad\` 后,
  Capture 每次启动自动加载(官方 autoload 机制),连回 bridge 并执行下发的 TCL。
- `bridge.py`/`server.py` 在 MCP 服务器进程内完成 TCP 桥接,无需单独服务。
- 所有能力都来自 OrCAD 官方接口,详见官方手册
  《OrCAD Capture Tcl/Tk Extensions》(`tools/extract_manual.py` 可提取为可检索文本)。

## 安装 / Install

前提:Windows + OrCAD 16.x(含 Capture 与 PSpice)、Python 3.10+、MCP 客户端(如 ZCode)。

```bat
git clone https://github.com/<USER>/orcad-mcp.git
cd orcad-mcp
pip install -r requirements.txt

:: 1) 安装 TCL agent 到 capAutoLoad(随 Capture 启动自动加载)
python install_agent.py

:: 2) 可选:提取官方手册供 AI 检索 API(需要 pypdf)
python tools\extract_manual.py

:: 3) 在 MCP 客户端中注册(以 ZCode 为例,~/.zcode/cli/config.json)
::    "mcp": { "servers": { "orcad-capture": {
::      "command": "python", "args": ["<repo路径>\\server.py"] } } }
::    重启客户端后,`mcp__orcad-capture__*` 工具自动可用。
```

## 工具一览 / Tools(14 个)

| 工具 | 说明 |
|---|---|
| `capture_status` / `bridge_diagnostics` | agent 连接状态 / PING 延迟 |
| `com_launch_capture` / `com_quit_capture` | COM 拉起 / 关闭 Capture |
| `tcl_eval` | **万能通道**:在 Capture 进程内执行任意 TCL |
| `tcl_api_search` | 在官方手册提取文本中检索命令(附录 A/B/C 全集) |
| `list_designs` / `list_pages` / `list_parts` | 设计 / 页 / 元件清单(含引脚坐标) |
| `get_part_properties` / `set_part_property` | 按位号读写元件属性 |
| `open_design` / `save_design` | 打开 .dsn / 保存 |
| `run_menu` | 触发任意菜单命令(如 `Tools::Annotate`) |

## 快速上手 / Quick start(对话示例)

- 「启动 Capture 并打开 `D:\x\demo.dsn`,列出所有元件」
- 「把 U1 的 VALUE 改成 74HC04 然后保存」
- 「按 PDF 实验讲义画一个 BJT 共射极放大电路并仿真」→ 见 `examples/exp3_bjt_ce/`
- 「把所有元件的 PCB Footprint 批量填上」→ AI 自动组合 `tcl_eval` + Dbo API 完成

## 实战经验(API 笔记)/ Hard-won API notes

以下是踩坑总结,写脚本前必读(更完整的工作流见 `examples/exp3_bjt_ce/`):

- **放置元件**:`PlaceNew <olb路径> <件名> 0` 进入放置模式 → 真实鼠标点击提交 → `EndPlace`
  结束。Macro Player 的 `PlacePart(x,y,...)` 对未注册到工程的库会静默失败。
- **移动/旋转**:`Move`/用户命令不可靠,直接用 Dbo 对象方法
  `$inst SetLocation [DboTclHelper_sMakeCPoint x y]`(整数 doc 单位,100/英寸)和
  `$inst SetRotation 0..3`。
- **引脚真实页面坐标**:用 `$pin GetOffsetHotSpot $st`(GetStartPoint 是符号坐标系);
  **页面坐标 y 向下**(Vcc 用小 y,地用大 y)。
- **改属性/位号**:`$inst SetEffectivePropStringValue name value`,位号属性名是 `Reference`。
- **source 库元件**(VSIN/VDC)无法 PlaceNew → 从自带 VSIN 的设计(如 learning resources
  的 accircuits.dsn)同设计 `$page NewPlacedInst $src $st $offset` 复制,再用 SetLocation 摆位。
  VSIN 设 `VOFF=12, VAMPL=0` 即等效 12V 直流源。
- **修改模型参数(如 β=70)**:复制 eval.lib 的 .MODEL 改 `Bf=70`,以 **`.INC` 后置引入**
  即可覆盖(`.LIB` 后置定义不生效);并给本机补建 `tools/pspice/library/nom.lib`
  (Lite 安装缺失,内容一行:`.lib "nom_eval.lib"`)。
- **模态对话框会饿死 TCL 事件循环**(agent 假死)。外部脚本应带一个 win32 对话框收割线程:
  含 "recovered"→点否,含 "Save changes"→点是,其余点确定;按钮文本要子串匹配(`否(&N)`)。
- **仿真的两种跑法**:Capture 内 `Menu "PSpice::Run"`(需 profile),或直接命令行
  `pspice\psp_cmd.exe -r file.cir`(.out 格式与 GUI 完全一致,更适合 AI 消费)。
- **获取命令词汇**:`SetOptionBool Journaling TRUE` 后,任何 UI 操作都会以 TCL 形式
  记录到 `%TEMP%\CAPTURELOG\OrCaptureLogFile.captcl`——照抄即可复现。

## 示例 / Examples

[`examples/exp3_bjt_ce/`](examples/exp3_bjt_ce/) — 完整实战脚本:按实验讲义自动完成
「绘制 BJT 共射极放大电路(β=70)→ Bias Point + 瞬态两种仿真 → 导出工作点文本与波形 PDF」。
端到端运行结果:ICQ=2.51mA(目标 2.5mA),Av≈81(带载 RL=2k)。

## 兼容性 / Compatibility

- OrCAD Capture / PSpice **16.6 Lite**(其它 16.x 大概率可用,欢迎反馈)
- Windows 10/11;Python 3.10+;MCP 客户端任意(stdio)
- 若你的 Capture.exe 被设置了"以管理员运行"兼容性标记,COM 拉起会失败
  (报 ERROR_ELEVATION_REQUIRED)——删除该标记或改用 UAC 方式启动。

## 免责声明 / Disclaimer

本项目仅通过 OrCAD 官方文档化的自动化接口(Tcl/Tk、COM)操作用户本机已安装的软件,
不分发、不修改任何 Cadence 二进制或受版权保护的文档。OrCAD/PSpice 是 Cadence Design
Systems 的商标。请遵守你所安装软件的许可协议。

## License

[MIT](LICENSE)
