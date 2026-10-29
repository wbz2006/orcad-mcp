---
name: orcad-automate
description: AI 直接操作 OrCAD Capture CIS / PSpice 的完整方法论与工具集(画原理图、改属性、跑 Bias Point/瞬态仿真、按实验手册复刻并从软件自身导出结果)。凡是用户提到 OrCAD、Capture、PSpice、画电路图/原理图、EDA 仿真、bias point、静态工作点、元件属性批量修改、.dsn/.opj 工程,或要求"让 AI 操作电路软件"——即使没点名 OrCAD——都应加载本 skill。配套开源工具:https://github.com/wbz2006/orcad-mcp
---

# OrCAD Capture / PSpice 自动化

让 AI 直接驱动 OrCAD Capture CIS 16.x 画图、改图、仿真、并**从软件自身导出**结果。
全程只走官方自动化接口(内嵌 Tcl/Tk + COM + psp_cmd 命令行 + win32 打印自动化),
不逆向不修改二进制。

## 0. 工具从哪来

本机标准安装位置:`D:\Main_FIles\free-deng\orcad-mcp\`。开源仓库:
https://github.com/wbz2006/orcad-mcp (新机器先 clone + `pip install -r requirements.txt` +
`python install_agent.py`)。

三段式链路:**MCP 客户端 → server.py(FastMCP, 常驻 TCP 5177)→ TCL agent(Capture 进程内)**。
优先用 MCP 工具(`mcp__orcad-capture__tcl_eval` 等);没有 MCP 客户端时
`import bridge; bridge.Bridge().ensure(); b.session().eval(tcl)` 亦可
(注意 agent 默认连 5177,除非启动 Capture 的进程环境带了 ORCAD_MCP_PORT)。

关键脚本(实验手册复刻全流程已固化,均在 orcad-mcp 根目录):
- **`orcad_quiet.py` — 安静模式(默认):全程窗口消息驱动,不抢焦点不置顶不动鼠标**,
  标注用 pymupdf 叠写到打印出的 PDF 上。用户可同时正常使用电脑。CLI:
  `python orcad_quiet.py --dat tran.dat --out 图.pdf --traces V(Vs) V(Vi) V(Vo) --caption "..." --name "信255 王保哲" [--two-frame]`(需 PSpice/Probe 已开)。
- **`cap_open.py <opj>`** — 冷启动打开工程:自动继承 `ORCAD_MCP_PORT`,按消息处理
  启动/恢复对话框,报告标题与活动 MDI 子窗口。
- **`cap_activate.py [PAGE1]`** — 消息驱动激活原理图页(SelectPMItem + 给项目树
  PostMessage 回车),解决 `GetActivePage` 报 "Command Requires SchematicView"。
- **`quiet_print.py <窗口标题前缀> <out.pdf>`** — 对 Capture / PSpice A/D / Probe
  任意已打开文档做消息驱动打印到 PDF(File>Print→BM_CLICK→Save As 填路径)。
- `probe_export.py` — 物理点击模式(需要前台,仅限用户可让出电脑时;Probe 内原生标注)。
- `tcl/prep_ic_loaded.tcl` — 参数化 IC 档切换(Rb1/VAMPL/RL/别名改名,带回读)。
- **`capture_guard.py` — 卡顿/意外弹窗防护(所有长流程必用)**:
  `eval_safe(s,tcl)`(超时→自动收割意外弹窗→重试;agent 断线→等 4s 自愈;
  TCL 脚本错误→立即抛,不浪费重试)、`reap()`(按语义表收割 #32770)、
  `save_verified(s,dsn)`(File::Save + **mtime 核验落盘**)、
  `health([dsn])`(进程/假死/僵尸/残留锁/agent RTT 一屏体检)。
  CLI: `python capture_guard.py health <dsn路径>` / `reap [--dry]`。
- **`sch_connectivity_audit.py` — 原理图连通性裁决标准(画完必跑)**:并查集引脚级审计
  (引脚热点↔导线端点↔结点),报告悬空引脚/T触无结点/十字交叉。目视与放大 PDF 都有盲区
  (V1 负极红竖线曾被误读为电池符号图形)。
- `print_export.py` / `cap_print.py` — 打印底层函数、Capture 重启恢复(旧路径)。
- `examples/exp3_bjt_ce/` — 画图/连线/属性的历史脚本(`tclrun.py` 可跑无 BOM 的 .tcl)。

## 1. 连接与页面

1. Capture 已在运行:直接用 MCP 工具。没运行:用 **`cap_open.py <opj>`**(内部
   `subprocess.Popen([Capture.exe, opj], env=...)`)→ 自动处理启动/恢复对话框
   (两种:确定/取消 与 是/否,ORCAP-1680)→ 等标题出现 .opj。
   **`ORCAD_MCP_PORT=5178` 必须在 `import bridge` 之前设置,且必须传给 Capture 进程环境**,
   否则 agent 连默认 5177、本地 bridge 在 5178 → `session()` 永远超时(冷启动第一坑)。
2. **TCL 需要 SchematicView**(GetActivePage 报 "Command Requires SchematicView" 时):
   `SelectPMItem {PAGE1}` 只选中树节点,**还要给 `SysTreeView32` 子窗口
   `PostMessage WM_SETFOCUS` + `WM_KEYDOWN/WM_KEYUP VK_RETURN`** 才真正打开/激活页面
   (全消息驱动,无需前台/鼠标;`cap_activate.py` 已封装)。比点 workbook 标签可靠。
3. **恢复对话框按钮语义**:标题 `OrCAD Capture CIS`、只有 确定/取消 的那个 = 上次异常
   关闭提示,点**确定**即加载磁盘态(点取消会留在 Start Page);标题带 ORCAP-1680、
   按钮 是/否 的才是"是否恢复未保存修改",按需选否。
4. Capture 的 "Start Page" 内嵌浏览器会**周期性抢前台/z 序**——自动化前关掉它;
   不参与交互的窗口降 NOTOPMOST(两个 TOPMOST 窗口会互相压盖)。
5. **agent 假死 = 有模态对话框**。ORCAP-1680 恢复询问等对话先处理再发 TCL;
   TCL 超时(30s)基本=被模态框卡住,枚举 #32770 处理后重试。
6. **`.opj` 可能被降级**:崩溃/异常打开后 Design Resources 与 schematic Doc 会丢
   (工程树变空),`git checkout -- xx.opj` 恢复;`.DSN` 同理,以 git HEAD 为准。

## 2. 画电路与改电路

- 建页/放置/连线/属性的基础配方见 references/api-notes.md(准确签名与坐标约定)。
- **改参数(R VALUE/VAMPL/别名改名)用 DBO SetEffectivePropStringValue/SetName——安全,
  多次验证**;改完 **F5** 才刷新视图,勿以屏幕判断 DB 状态。
- **结构性修改(删元件/删线/建线)严禁 DBO 写操作**(DeleteWire/NewWireScalar/
  DeletePartInst 会破坏 DB 一致性 → 保存时 **Capture 崩溃退出**,已复现×2)。
  必须走 Capture 原生事务:DBO 只读拿 ID → `SelectObjectById <id>` +
  `Menu "Edit::Delete"`;建线用官方 `PlaceWire x1 y1 x2 y2`(英寸,y 向下)。
  崩溃后:删 .DSNlck → 重启 opj → ORCAP-1680 选"否"加载磁盘态 → 重做。
- "删除电阻并桥接"实测配方:DBO 只读拿到两端导线 ID 与 Rs 元件 ID →
  原生 Delete×3 → PlaceWire 桥接 → 值类 DBO 修改 → **保存**。
- **保存**:`Menu "File::Save"` 的历史崩溃与 DBO 结构性写同源——纯原生事务流程下
  (实验4)已连续稳定使用数十次。可靠姿势 = **`save_verified(s, dsn)`**(内部
  File::Save + 等 .DSN mtime 前进,被弹窗挡住时给诊断);批量改动后也可
  `$pg MarkModified` + 前台 Ctrl+S。**窗口标题没有 `*` 不代表已保存,以 mtime 为准**;
  save_verified 返回 "no-change" = 无修改可存,不是故障。
- **卡顿治理三守则**(模态框/假死/僵尸是"卡很久"的全部根因):
  1. **所有 eval 走 `eval_safe`**,裸 eval 超时 30s×N 次循环就是"卡很久"的主因;
  2. **批量操作前先 `health(dsn)` 体检**(僵尸进程/残留锁/假死提前现形);
  3. **恢复阶梯**:reap(清意外弹窗)→ health 看假死/僵尸/残留锁 →
     `taskkill /IM Capture.exe /F` + 删 .DSNlck + `cap_open.py` 重启。
     每一步等待都必须有 deadline,禁止无上限的 while 轮询。
- **旋转**:`$inst SetRotation 0..3` 会把位号/值文本一起转,且**不能修复"文本竖排"**
  (见 api-notes 已知缺陷)。已放置元件位置用 `SetLocation`;方向尽量在
  `NewPlacedInst` 的 rotation 参数一次定好,不要事后再转。

## 3. 仿真与导出(软件自身打印管线)

- **仿真**:手写 .cir(**注释一律 ASCII**——psp_cmd 把 UTF-8 中文当 ANSI 读,乱码会印进
  报告)→ `tools\pspice\psp_cmd.exe -r file.cir` → .out/.dat。
  .PRINT TRAN V[node] 用**方括号**;.OP 出静态点。
- **文字结果打印**(bias N.out):PSpice A/D File→Open .out → File→Print →
  Save As 填全路径(此对话框无 Plots 列表,OK 位置也不同)。
- **波形打印**:默认走 `orcad_quiet.py` CLI(全消息驱动,标注 PDF 叠写);需要
  Probe 内原生标注时才用 `probe_export.py`(前台物理模式)。流程:File→Open .dat →
  Trace→Add Trace → 双坐标系:先加前 N-1 条,Plot→Add Plot to Window,再加最后一条
  (新框在顶部)→ 物理模式用 Plot→Label→Text 标注(**OK 后状态栏 "Move the text..."
  必须物理点击放置,这样才进打印**)→ File→Print。
- **铁律:打印前把 Probe 关到只剩目标窗口**(Ctrl+F6 循环+Ctrl+F4)。
  打印对话框 "Plots to Print" 列表(多选)的消息选择(LB_SETSEL+LBN_SELCHANGE)
  在多窗口时不可靠,单窗口时确定。
- **Capture 原理图打印**:激活 PAGE1(SelectPMItem+Enter)→ File→Print(该对话框
  无 Plots 列表,OK 按钮 id=1)→ Save As。`quiet_print.py "OrCAD Capture" out.pdf`
  一条命令完成;`quiet_cap_print.py` 是先切页再打印的示例。
- **文字/波形打印同理可全消息驱动**:`quiet_print.py "PSpice A/D" bias.pdf` 打活动
  子窗口;`orcad_quiet.py` CLI 负责 Probe(开关窗/加轨迹/双坐标系/打印/PDF 叠写标注)。
- Save As 对话框:首个可见 Edit `WM_SETTEXT` 全路径 + 向对话框
  `WM_COMMAND IDOK`(**不要按回车**,回车会抢前台);先删目标 PDF 防覆盖确认。
- 每份 PDF 打完用 pymupdf 渲染成图核验内容(**打印内容≠屏幕所见**,必须核验)。

## 4. 学习新命令

- `tools/extract_manual.py` 提取官方 922 页手册 → 全文可 grep;
- 在 Capture 命令窗执行 `SetOptionBool Journaling TRUE`,UI 操作会记录 TCL 到
  `%TEMP%\CAPTURELOG\OrCaptureLogFile.captcl` —— 照抄即可复现。

## 5. 常见故障速查

| 症状 | 原因/处理 |
|---|---|
| eval 一卡 30 秒、反复超时 | 模态框饿死 agent;用 `eval_safe`(自动 reap+重试),禁止裸 eval 循环 |
| Capture 整个无响应(消息也不回) | 主窗口假死 IsHungAppWindow;消息路径已无效 → taskkill+删锁+cap_open.py |
| tasklist 里多个 Capture.exe | 僵尸进程干扰判断;`health()` 列出,杀掉非窗口属主再操作 |
| 保存后不确定存没存上 | `save_verified` 看 .DSN mtime;标题无 `*` 不可信 |
| 冷启动后 session() 一直超时 | Capture 进程环境没带 `ORCAD_MCP_PORT`(agent 连了 5177);用 `cap_open.py` |
| agent 连不上/断开 | 模态对话框(先枚举 #32770 处理);端口被 MCP server 占用(直接用 MCP 工具) |
| TCL 超时 30s | 被模态框卡住;枚举 #32770 → 读文本 → 点正确按钮 |
| `invalid command name "\ufeffset"` | .tcl 被 PowerShell 写成 UTF-8 **带 BOM**;读时 `utf-8-sig` 或存 ASCII |
| Command Requires SchematicView | 页面未激活:SelectPMItem + 给 SysTreeView32 PostMessage 回车 |
| 打印出来的是旧窗口 | Plots to Print 列表没选对 → **关到只剩目标窗口** |
| 标注没进打印 | 没走 move-mode 放置;或锚点在可视区外(改量程后);安静模式改 PDF 叠写 |
| 保存时 Capture 崩溃 | DBO 结构性写操作或 `Menu File::Save` → 原生事务 + MarkModified + Ctrl+S |
| 工程树空白 / 丢了 Design Resources | 崩溃后 `.opj` 被降级 → `git checkout -- xx.opj` |
| COM ELEVATION_REQUIRED | 删 Capture.exe 的 RUNASADMIN 兼容标记 |
| 提权窗口在前台时鼠标/前台 API 全返回 0 | 中完整性进程不能操作管理员窗口;物理输入用 `pythonw elev_run.py` 提权 |
| 物理点击坐标偏 1.5 倍 | 进程 DPI 非感知:逻辑坐标 = 物理/1.5(或调用 SetProcessDpiAwareness) |
| 字母快捷键被吞 | 中文输入法;先 Shift 切英文再发按键 |
| 网表 Cannot open nom.lib | 补建指向 nom_eval.lib |
| .PRINT 节点全对却没数据 | 检查 .cir 里节点名与打印名一致;注释勿用中文(乱码进 PDF) |

## 6. 已知未解决问题

- **复制/新建元件的位号与值文本竖排**(如 RL 复制 Rb1):DB 里 `GetRotation`、
  显示属性 rotation/location 与正常件完全一致;重放新件、prop rot 0..3、
  `ResetAllDisplayPropertiesFontToDefault` 均无效;`SetFont(LOGFONT)` 直接崩 Capture。
  暂时接受(打印 PDF 可见,已交付图件带此缺陷),不要在交付前为此反复重做设计。
- Capture 的 `Menu "File::Save"` 崩溃原因未定位;用 MarkModified + Ctrl+S 规避。
