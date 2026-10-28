# OrCAD MCP 项目交接提示词(2026-10-28)

> 给接手 AI 的话:本文是唯一需要的上下文。项目 = 用 AI 直接操作 OrCAD Capture CIS 16.6 Lite(画原理图/跑 PSpice 仿真/导出实验材料)。基础设施已建成并开源,当前在收尾"实验3:BJT 共射极电压放大电路"的交付。先通读本文,再动手。

## 1. 资产地图

| 项 | 路径 |
|---|---|
| orcad-mcp 仓库(本地工作副本) | `D:\Main_FIles\free-deng\orcad-mcp` |
| GitHub(公开,已配推送权 wbz2006) | https://github.com/wbz2006/orcad-mcp |
| **实验交付目录(用户要看的东西在这)** | `D:\Users\Download\exp3_BJT_CE\` |
| 方法论 Skill | `C:\Users\wbz\.agents\skills\orcad-automate\`(SKILL.md + references/api-notes.md,完整 API 笔记) |
| OrCAD 安装根 | `C:\OrCAD\OrCAD_16.6_Lite` |
| PSpice 命令行引擎 | `<根>\tools\pspice\psp_cmd.exe` |
| TCL agent(已装入 capAutoLoad,随 Capture 自启) | `<根>\tools\capture\tclscripts\capAutoLoad\orcad_mcp_agent.tcl` |
| 元件符号库 | `<根>\tools\capture\library\pspice\{analog,source,eval}.olb`、`<根>\tools\capture\library\capsym.olb`(地/电源符号) |
| 手册提取文本(可 grep 的官方 922 页 API 手册) | 仓库 `docs\`(没了就跑 `python tools\extract_manual.py` 重新生成) |

实验目录内容:`EXP3.DSN`/`exp3.opj`(工程,SCHEMATIC1/PAGE1=实验电路)、`bias.cir`/`tran.cir`(+`.out`/`.dat`,psp_cmd 真实仿真产物)、`q2n3904_bf70.inc`(β=70 模型)、图3.1/3.2/3.4、表3.1、`实验说明.md`、`pins.json`(12 元件引脚真实页面坐标)、`existing_wires.json`。

环境:Windows 11 + Git Bash;Python 3.14(`C:\Python314\python.exe`,已装 pywin32/mcp<2/matplotlib/numpy/pypdf/olefile/Pillow);中文文件名正常,但**写 .txt 交付物用 GBK 编码**。

## 2. 架构与连接(必须先懂)

```
ZCode ─MCP─▶ server.py ─TCP 5177─▶ TCL agent(Capture 进程内,事件驱动)
构建脚本 ────TCP 5178───────────────┘
```

**端口铁律**:ZCode 注册的 orcad-capture MCP 服务器占 5177,脚本必须用 `ORCAD_MCP_PORT=5178`,且必须在 `import bridge` 之前设置。

标准启动样板(照抄):

```python
import sys, os, time
BASE = r"D:\Main_FIles\free-deng\orcad-mcp"
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.chdir(os.path.join(BASE, "examples", "exp3_bjt_ce"))
os.environ.setdefault("ORCAD_MCP_PORT", "5178")   # import bridge 之前!
import bridge as br, draw_exp3 as dx
from build_exp3 import parse_insts, TCL_LIST_INSTS, SET_ROT_HELPER, find_click_point, click
dx.ensure_capture()          # 起 bridge→COM 拉 Capture→等 agent(≤180s)→对话框收割线程
s = br.BRIDGE.session()
```

- `draw_exp3.py`:`ensure_capture()`、`SETUP_TCL`(orCStr/orGetPage)、对话框收割线程
- `build_exp3.py`:`SET_ROT_HELPER`(orSetLoc/orSetRot/orSetRef)、`TCL_LIST_INSTS`+`parse_insts`(元件/引脚清单)、`find_click_point`/`click`
- `v5_wires.py`:**幂等批量操作模板**(崩溃自动重启会话+进度文件续跑)——任何批量 Place 都照这个模式写
- agent 断线 4s 自动重连;Capture 崩溃后 `ensure_capture()` 重拉;`s.eval(tcl, timeout)` 抛 RuntimeError=TCL 错

**激活页面窗口**(多数用户命令的前提,常失效要重跑):

```python
s.eval('SelectPMItem {PAGE1}', 60)
import win32gui, win32con, win32api
frame = win32gui.FindWindow("OrCaptureFrame", None)
win32gui.SetForegroundWindow(frame); time.sleep(0.5)
win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
time.sleep(3)
# 验证 GetActivePage 非 NULL
```

## 3. 核心 API 速查(全部实测;完整版见 skill 的 api-notes.md)

| 任务 | 正确做法 | 陷阱 |
|---|---|---|
| 放元件 | `PlaceNew <olb绝对路径> <件名> 0` → **真实鼠标点击**视图区提交 → `EndPlace` | 落点=光标处;新元件检测用 **ID 差集**(放置前后 `parse_insts` 的 id 集合差),别用坐标猜 |
| 移动 | Dbo `orSetLoc id x y`(英寸,绝对) | 用户命令 `Move` 不可靠,禁用 |
| 旋转 | Dbo `orSetRot id 0..3` | — |
| 改位号/属性 | `SetEffectivePropStringValue`(位号属性名=`Reference`;R/C 值=`VALUE`;VSIN=`VOFF/VAMPL/FREQ`;VDC=`DC`) | — |
| 引脚真实页面坐标 | `$pin GetOffsetHotSpot $st` | `GetStartPoint` 是符号系,别用 |
| 连线 | `PlaceWire x1 y1 x2 y2`(英寸);T 接点补 `PlaceJunction` | **页面 y 向下**;PlaceWire 坐标=英寸 |
| 地/电源符号 | `PlaceGround x y <capsym.olb绝对路径> GND_POWER 0` | — |
| 网络别名/文字 | `PlaceNetAlias x y 名`、`PlaceText x1 y1 x2 y2 文本` | — |
| 删除对象 | `SelectObjectById id` + `Menu "Edit::Delete"` | — |
| 保存 | **DB 改动后先 `$pg MarkModified`,再给窗口发 Ctrl+S**(实测 1s 内落盘) | `Menu "File::Save"` 在本设计上多次引发 "application has quit unexpectedly";DB 级 SetLocation/NewWireScalar 不会把设计标记为已修改,不 MarkModified 时 Ctrl+S 是空操作 |
| 列元件/引脚 | `TCL_LIST_INSTS` + `parse_insts` | — |
| 仿真 | `cd 实验目录 && psp_cmd.exe -r bias.cir`(tran 同理) | Capture 内 `Menu "PSpice::Run"` 在 TCL 会话永远禁用;β 覆盖必须用 `.INC` 后置(`.LIB` 后置无效);`.PRINT` 节点电压用**方括号** `V[node]` |
| TCL 里拼 Python 字符串 | 用 `.replace("%占位%")`,**不要 f-string**(花括号地狱) | — |
| 脚本变量 | TCL 里先 `set st [DboState]`(SETUP_TCL 只保证 orCStr 等) | `_st` 未定义是最常见报错 |

## 4. 禁忌(违反=视图永久损坏/丢数据)

1. **绝不调用 ZoomScale/ZoomArea/ZoomAll/ZoomSelection**——会把页面视图渲染"毒化"(卡死在 1045% 空白角)且**持久化进 DSN**,重开无效,只能换底图重建。已为此重建 3 次。
2. 不要强杀 Capture 而不保存(会弹恢复对话框);收割线程规则:对话框含 "recovered"→否 / "Save changes"→是 / 其他→确定(按钮文本带 `(&N)` 后缀,用子串匹配)。
3. 连续 PlaceWire 可能随机崩 Capture——批量操作必须用 v5_wires.py 的幂等+断点续跑模式。
4. 不要往 ZCode 的 5177 端口绑 bridge(SO_EXCLUSIVEADDRUSE 会报错)。
5. 模态对话框存在时 TCL 事件循环饿死(agent 连不上=先查对话框)。
6. 交付物 .txt 用 GBK 写;截屏前先最小化 ZCode/Agent HUD(置顶窗口会抢前台,或用 `SetWindowPos(probe, HWND_TOPMOST, ...)` 压住)。
7. **不要用 `$pl GetDisplayProp [DboTclHelper_sMakeCString "Value"] $st`**——实测直接令 Capture 崩溃
   (报 "application has quit unexpectedly")。要动属性文字位置,先在隔离工程里验证正确 CString 传法。
   Capture 崩溃后的恢复:关崩溃框→杀僵尸进程→COM 重拉→"detected projects"/"recovered...save?" 都选
   是/确定,重开后用 bridge 复核 globals/wires 数量。
8. **绝不用 DB 级 `$pg DeleteWire` / `$w ...` 删导线**——当场不报错,但**下一次保存时 Capture 直接静默退出**
   (无对话框、无崩溃提示),未保存改动全丢。删线唯一安全路径:`SelectObjectById <wireId>` + `Menu "Edit::Delete"`
   (见 `ui_del.py`,已对含引脚/结点的导线验证)。
9. `AddJunctionToWire` / `$w NewJunction` 是**延迟生效**的:调用后导线不会立即分段、`GetConnectionCount` 也不变,
   必须 `MarkModified` + Ctrl+S 保存后才生效(保存后母线才被切开、连接数才从 1 变 3)。
10. `SetLocation` 移位后**必须重开工程**(close→open)才会重画元件体;不重开就截图,会看到旧位置残留元件体、
    新位置只剩引脚(表现为"电阻没有锯齿")。

## 5. 当前精确状态(截至交接)

**电路(EXP3.DSN / SCHEMATIC1/PAGE1,已保存)**:✅ 完成——12 元件全部就位(真 **VDC** Vcc=12V、真 **VSIN** Vs=5mV/1kHz、Rs=1k、C1=10uF、Rb1=57k、Rb2=30k、Rc=2k、Q1=Q2N3904 β=70、Re=1k、Ce=47uF、C2=10uF、RL=2k);全图在 Letter 页内(y 向下:+12V 母线 y=1.9、基极母线 y=3.9、集电极节点 y=3.2、发射极母线 y=4.6、**底部地母线 y=5.9**)。

**布局(2026-10-28 13:40 按实验 PDF 第 8 页示例图重排,已保存)**:Vs `loc=(80,490)`、Rs `(190,380)`、C1 `(260,380)`、Rb1 `(320,250)`、Rb2 `(320,459)`、Q1 `(430,380)`、Rc `(430,250)`、C2 `(630,310)`、Re `(430,480)`、Ce `(620,480)`、RL `(830,300)`、Vcc `(890,190)`、GND `(430,590)`(hotspot 440,590)。即:Vs 左下、Rs/C1 与基极同高、Rb1/Rb2 在基极左侧上下、Rc 在集电极正上方、C2 在集电极节点高度、RL 右侧、**Re 在发射极正下方、Ce 在发射极节点横线右端**、Vcc 右上角、GND 在 Re 正下方。**29 根导线 / 12 元件 / 1 接地**;连接数复核:900,190=2 / 900,230=2 / 90,480=2 / 90,520=2 / 90,590=2 / 330,190=2 / 440,190=3 / 440,320=3 / 440,410=2 / 440,470=3 / 440,510=2 / 440,590=4 / 630,470=2 / 630,500=2 / 630,590=3 / 330,390=4 / 330,590=3 / 840,590=3 / 840,320=2;37 个导线端点无悬空。电容值已改为 `10uF`/`47uF`(PSpice 复跑结果不变:Vo=168.95mV、Av=81.2)。

**接地结构(2026-10-28 追加,按实验 PDF 参考图)**:不再用 6 个独立地,改为**一条公共地母线 + 1 个 GND**——Vcc 在右上角 `loc=(890,190)`(+ 引脚 900,190 接顶部母线、− 引脚 900,230 沿右侧下到地母线);地母线 `90,590 → 900,590`,Vs− (90,520)、Rb2 (330,489)、Re (570,510)、Ce (630,500)、RL (840,330)、Vcc− (900,230) 全部接母线;唯一 GND 在 `loc=(560,590)`(hotspot 570,590,即 Re 正下方)。视觉复核截图 `screen48.png`,交付图由它裁出(crop `(566,452,1940,1136)` → 1374×684,左下"班级/姓名"占位已抹白并补回地母线像素)。注意:Vcc 原在 x=950 时会画到图框外,故内移到 900。

**仿真(已跑通,真实引擎)**:bias.out(IB=45.6µA、**IC=2.51mA**、VCE=4.44V、VBE=0.689V、总功耗 31.9mW)+ tran.out/tran.dat(5001 点;Vi=2.08mV→Vo=169mV,**Av≈81** 反相)。

**交付物现状(2026-10-28 11:25 已全部更新)**:
- 图3.2 ✅ 完整数据(SMALL SIGNAL BIAS SOLUTION 全节点电压表 B/C/E/Vi/Vo/Vs/Vcc、VOLTAGE SOURCE CURRENTS、TOTAL POWER DISSIPATION、OPERATING POINT、BJT 全表含 CBE/CBC/FT/BETAAC)+ 署名"信255 王保哲"(GBK)
- 图3.1 ✅ 已用 `screen48.png` 重裁(crop `(566,452,1940,1136)` → 1374×684),共地母线 + PDF 示例图布局版本;左上角标注"班级:信255  姓名:王保哲",左下"班级/姓名"占位已抹白并补回地母线像素
- 图3.4 ✅ tran.out 真数据 matplotlib PDF(Probe 自动化加轨迹此版本走不通,实验说明里有 30 秒手动步骤)
- 表3.1 ✅ 署名已改"信255  王保哲"(GBK 重写)
- 实验说明.md ✅ 已同步(图3.2 完整、缺线修复、GND 对齐、仿真 profile 说明、10uF/47uF 记法、PDF 示例图布局)
- **接地修正 → 已改为共地母线(2026-10-28 12:00)**:用户指出与实验 PDF 不一致(PDF 是"所有元件共用一个地")。
  已删除 5 个独立 GND、加底部公共地母线、Vcc 移到右上角(见 §5"接地结构")。
  本轮脚本:`examples/exp3_bjt_ce/stepA~stepD.tcl`(旧批量)、`m1.tcl`/`m2.tcl`(Vcc 内移)、
  `markpage.tcl`(MarkModified)、`save_ui.py`(Ctrl+S 落盘并校验 mtime)、`conn2.tcl`(连接数复核)、
  `shot48.py`/`mkfig.py`/`deliver_fig.py`(截图→裁剪→出图)。
- **布局重排 + 电容补 F(2026-10-28 13:0x)**:用户要求元件相对位置与 PDF 第 8 页示例图一致、电容值补 "F"。
  - 元件用 `SetLocation` 移位(`v3_moves.tcl`/`v5_moves.tcl`);**移位后必须重开工程才会重画元件体**,
    否则截图里旧位置残留元件体、新位置只剩引脚(第一次截图就是这样,重开后正常)。
  - 删旧导线只能用 UI 路径:`ui_del.py`/`ui_del2.py`(`SelectObjectById` + `Menu "Edit::Delete"`);
    **DB 级 `$pg DeleteWire` 会让 Capture 在下次保存时静默退出**。
  - 加线用 `NewWireScalar`(`v4_addin.tcl`/`v6_addcol.tcl`);结点用 `$pg AddJunctionToWire`(或 `$wire NewJunction`),
    **调用后 wire 不会立刻分段、`GetConnectionCount` 也不更新,必须 MarkModified+Ctrl+S 后才生效**
    (保存后 440,190 从 1 变 3、母线才被切成两段)。
  - 电容值 `SetEffectivePropStringValue VALUE` 改 `10uF`/`47uF`(`v1_caps.tcl`);`bias.cir`/`tran.cir` 同步改 uF 并复跑,
    结果完全一致(IC=2.51mA、Vo=168.95mV、Av=81.2),图3.2/图3.4/表3.1 由 `gen_final.py` 重新生成
    (图3.4 署名改为"班级: 信255   姓名: 王保哲")。
  - 图3.1 由 `mkfig3.py` 重裁(见 §5)。
- exp3.opj 实际**已含** Bias/Tran 两个 profile(恢复重开后被重写,GlobalState 用绝对路径,无害)

**仓库**:最新推送 `248f5e3`;HANDOFF.md 即本文。

## 6. 待办(2026-10-28 13:15 更新)

- ~~图3.1 更新~~ ✅ 已替换为共地母线 + PDF 示例图布局版本(见 §5)
- ~~表3.1 署名~~ ✅
- ~~实验说明.md 更新~~ ✅
- ~~接地结构改成 PDF 的共地母线~~ ✅(32 导线 / 1 接地,已 MarkModified+Ctrl+S 落盘并复核)
- ~~元件相对位置对齐 PDF 第 8 页示例图 + 电容值补 F~~ ✅
- **git 提交推送**(下一步):`git add -A && git -c user.name=wbz2006 -c user.email=wbz2006@users.noreply.github.com commit -m "..." && git push`
- 可选:给 `Vo` 补网络别名(图3.1 目前只有 Vi 可见;PDF 示例图有 Vo);skill api-notes 与记忆 `orcad-mcp-project.md` 补"保存丢线(existing_wires 差集补法)""GND hotspot 偏移 0.1""GetDisplayProp 崩溃""DB 改动后需 MarkModified 再 Ctrl+S""DeleteWire 后地母线会被结点分段"几条经验。

## 7. 快速命令备忘

```bash
# 仿真复跑(必须在实验目录下)
cd /d/Users/Download/exp3_BJT_CE && "/c/OrCAD/OrCAD_16.6_Lite/tools/pspice/psp_cmd.exe" -r bias.cir
# β=70: .LIB eval.lib 之后 .INC q2n3904_bf70.inc (后置 .MODEL 覆盖)
# 本机缺 nom.lib 已补建(指向 nom_eval.lib),别删

# 查 Capture/端口/对话框
tasklist //FI "IMAGENAME eq Capture.exe"
netstat -ano | grep 5178
# 对话框枚举: win32gui EnumWindows 找 #32770
```

## 8. 用户偏好(重要)

- 中文交流;交付物放下载目录 `D:\Users\Download\exp3_BJT_CE\`
- 用户会实际打开工程检查:电路必须**视觉完整、位置合理、打开即见**(不能要用户缩放找)
- 用户要求仿真结果是**软件真实导出**(psp_cmd 的 .out 是软件原生输出,可接受;Probe 窗口自动化加轨迹此版本走不通,已文档化 30 秒手动步骤)
- 署名:信255 王保哲
