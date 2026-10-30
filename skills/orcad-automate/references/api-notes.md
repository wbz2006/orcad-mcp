# OrCAD Capture 16.6 自动化 API 笔记(实测确认)

来源:官方《OrCAD Capture Tcl/Tk Extensions》(922 页,随产品附带)+ 逆向验证。
提取脚本:`tools/extract_manual.py`(生成 docs/appendixA/B/C 全集,可 grep)。

## 坐标与单位(最容易踩的坑)

- 页面坐标 **y 向下**:y 小 = 屏幕上方。Vcc/电源轨用小 y,地用大 y。
- doc 单位:100/英寸(粒度 `$page GetPhysicalGranularity`)。
- 各接口单位不同:
  - `PlaceWire/PlaceJunction/PlaceGround/PlaceNetAlias/PlaceText/PlacePart`:**英寸**(double)
  - Dbo `SetLocation`/`NewPlacedInst` 的 CPoint:**doc 整数**(英寸×100)
  - `Move dx dy 0`:**相对英寸**(但实测不可靠,勿用)
- 引脚真实页面坐标:`$pin GetOffsetHotSpot $st`(CPoint,doc);`GetStartPoint` 是符号系
  (旋转后不随页面变)。旋转 90° 后引脚绕符号体中心转(竖置 R 引脚跨 0.4")。

## 对象获取惯用法

```tcl
set _s $::DboSession_s_pDboSession
DboSession -this $_s
set st [DboState]
# 遍历设计 → 原理图 → 页
set dit [$_s NewDesignsIter $st]         ;# 设计名常为大写全路径,用 string match -nocase
# 页上元件:
set iit [$pg NewPartInstsIter $st]
set pl  [DboPartInstToDboPlacedInst $i]  ;# 转型,否则是基类
$pl GetReference $c;  DboTclHelper_sGetConstCharPtr $c   ;# CString 都这样读
```

- 未知对象的方法表:对它调 `ZZZBogus`,错误信息会列出全部合法方法名。
- 迭代器用完 `delete_DboXxxIter $it`;DboState 用 `[$st OK]` 判断。
- 脚本顶层 `return` 经 `uplevel #0` 会被 catch 判为错误——包一层 proc。

## 放置

- 可 PlaceNew 的库:`analog.olb`(R/C/L...)、`eval.olb`(Q2N3904...)、`breakout.olb`,
  路径 `tools\capture\library\pspice\`;**source.olb(VSIN/VDC)PlaceNew 必失败**;
  **capsym.olb**(地/电源符号)用 `PlaceGround x y capsym GND_POWER 0` / `PlacePower`。
- `PlaceNew <olb> <件名> [deviceIndex]` → 真实鼠标点击提交 → `EndPlace`。
  落点 = 当前光标的页面映射位置(固定光标则固定落点);之后 SetLocation 摆到位。
- Macro Player `PlacePart(x,y,lib,pkg,dev,bool6)` 对未注册库静默失败(Object Not Found)。
- 复制现有实例:`$dstPage NewPlacedInst $srcInst $st [CPoint]`(同设计可靠;
  ptOffset 是**相对源位置**的偏移,复制后 SetLocation 校正)。
- 符号件名带 `.Normal` 后缀(GetPart 需要:`R` → `R.Normal`)。

## 修改

- 属性:`$inst SetEffectivePropStringValue [CStr name] [CStr value]`
  位号属性名 = `Reference`;改完 `$pl GetReference` 回读验证。
- 位置:`$inst SetLocation [DboTclHelper_sMakeCPoint x y]`(doc 整数)。
  用户命令 `Move`/`SelectObjectById+Move` 在重开工程后经常静默失效,勿依赖。
- 旋转:`$inst SetRotation 0..3`(0=符号原始方向;R 原始为水平)。
- 模型参数:复制 eval.lib 的 .MODEL 改参数存 .inc,网表里 **`.INC` 后置覆盖生效,
  `.LIB` 后置不生效**。Lite 安装缺 `nom.lib` → 在 `tools/pspice/library/` 补建:
  一行 `.lib "nom_eval.lib"`。

## 工程结构

- `.opj` 是纯文本 s-表达式(可手工构造):ProjectType "Analog or A/D Mixed Mode" +
  `(File ".\x.dsn" (Type "Schematic Design"))` + PSpice Resources(仿真 profile 用
  `File.PSpice.{09528990-3187-11D2-BC7B-00A0C90CBF91}` 节点,ActiveProfile 指向 .sim)。
- `.dsn`:OLE 结构存储,不可手写 —— 复制现成 .dsn(如 learning resources 的
  accircuits.dsn)改名做底,再 NewSchematic/NewPage/SetRoot 换成自己的页。
- `.sim` profile 是文本(@Analysis: 0=瞬态 2=DC 3=Bias Point,`+0 "5ms"` 等字段);
  可手工构造,但 dsn 缺失时打开工程会弹 profile 初始化错误(模态!)。
- capAutoLoad 下所有 .tcl 启动自动 source(官方机制);agent 放这里。
- 本机 Lite 安装 **缺 nom.lib**(网表固定引用):补建 `tools/pspice/library/nom.lib`
  内容 `.lib "nom_eval.lib"`。

## 仿真

- 命令行:`tools\pspice\psp_cmd.exe -r file.cir`(.out/.dat 生成在 .cir 同目录)。
- .PRINT 语法:**节点电压用方括号 `V[node]` 或 `V[n1,n2]`**;圆括号 `V(x)` 是器件电压
  (会报 "Must be a two terminal device")。
- 模型覆盖:`.LIB eval.lib` + `.INC 覆盖.inc`(后置 .MODEL 生效)。
- Capture 内运行:`Menu "PSpice::Run"` —— 需要 PM 选中 profile 且无 TCL 上下文问题,
  经常报 Menu Disabled;命令行更可靠。
- Journaling:`SetOptionBool Journaling TRUE` → UI 操作记录 TCL 到
  `%TEMP%\CAPTURELOG\OrCaptureLogFile.captcl`。

## 稳定性

- **模态对话框阻塞 TCL 事件循环**(after/fileevent 全停)→ agent 假死。
  外部收割线程(win32 EnumWindows + BM_CLICK)是必需品;规则按语义:
  "recovered"→否 / "Save changes"→是 / 其他→确定;子串匹配按钮文本。
- 视图(ZoomScale/ZoomSelection/Menu View::Zoom)可能永久失效 —— 与 DB 无关,
  验证与导出全部走 DB + 外部渲染,不要依赖屏幕。
- Capture 的 COM `Quit()` 在部分场景抛错;taskkill /IM Capture.exe 兜底(注意先保存)。
- Capture.exe 的 RUNASADMIN 兼容标记会阻断 COM 启动(ERROR_ELEVATION_REQUIRED):
  删除 `HKCU\...\AppCompatFlags\Layers` 对应值。

## v4 实战补充(2026-10-28)

- **source.olb 可以 PlaceNew**:之前的失败是混乱会话(错误活动页/多工程切换)的副作用。
  在干净单工程会话、页面窗口激活、ID差集检测下,VSIN/VDC 均**一次成功**。
- **新元件检测必须用 ID 差集**(放置前后集合差),不要用坐标启发。
- **重复/多余实例可删**:`SelectObjectById id` + `Menu "Edit::Delete"`。
- **SNUBBER/accircuits 等教程设计的页面是巨页**(164×104"),复制底图后要
  `$pg SetPageWidth 11000 / SetPageHeight 8500` 改成 Letter(单位是 doc 0.01inch;1100/850 是错的,见"从零画整页原理图"节)。ABC.DSN 页面本身正常(1100×850)。
- **视图毒化**:ZoomScale/ZoomArea/ZoomAll/ZoomSelection 一旦调用,页面渲染可能永久冻结
  (保存进 DSN,重开依旧),且滚轮/键盘/TCL 缩放全部失效——**自动化中禁用一切缩放命令**。
- 跨设计 `NewPlacedInst(src, st, offset)` 实际可用(before/after 计数验证);
  offset 是相对源位置的偏移,复制后需 SetLocation。
- **元素删除**:`SelectObjectById` + `Menu "Edit::Delete"`(wire 也能删?未验证,元件已验证)。
- 打开第二工程后,活动页会漂移:GetActivePage 前先 CloseProject(第2个工程)再 SelectPMItem。
- PSpice::Run 菜单在 TCL 会话中始终 Disabled(原因未明);psp_cmd 命令行是可靠替代。
- Probe(tclscripts/pspAuto)支持脚本化,Add Traces 对话框可 win32 点击自动化,
  但表达式框 WM_SETTEXT 会被 MFC 重置,需真实键盘;时间预算内未走通,留待后续。

## 软件自身导出 PDF(打印自动化)——2026-10-29 全流程验证通过
工具:`orcad-mcp/print_export.py`(波形/bias/原理图三份 PDF)、`cap_print.py`(Capture 重启+切页+打印)。

- **菜单操作不要点屏幕坐标**:用 ctypes `GetMenu/GetSubMenu/GetMenuItemID` 枚举菜单树,`PostMessage(hwnd, WM_COMMAND, id, 0)` 异步触发(不会被模态对话框阻塞,SendMessage 会)。菜单文本匹配 `norm(s)=s.split('\t')[0]` 去掉 `&` 和尾点;注意 PSpice 菜单是 **"Add Trace..."(单数)**。
- **读控件文本**:MFC 对话框是 Unicode,`WM_GETTEXT` 缓冲按 `L*2` 字节 utf-16-le 解码再 `split('\x00')[0]`;按 `L` 字节切会把 ASCII 读成 `'A\x00n\x00…'` 乱码。
- **Probe 加轨迹**(旧法点列表项不可靠):Trace→Add Trace 对话框 → 对**最宽的可见 Edit**(Trace Expression, id=301)`WM_SETTEXT` 写表达式 → `WM_GETTEXT` 回读验证 → 对 id=1 按钮 `SendMessage(BM_CLICK)` → 轮询对话框关闭。三轨迹循环即可。
- **打印三步流**:PostMessage File>Print → 找 #32770 标题=="打印"/"Print" → 物理点击 OK(id=1 按钮,先 set_foreground)→ 等待"另存为/Save Print Output As" #32770 → 首个可见 Edit `WM_SETTEXT` 全路径 → 回车。**先删目标 PDF** 避免覆盖确认框。默认打印机 `win32print.SetDefaultPrinter("Microsoft Print to PDF")`。
- **bias 文本导出**:PSpice A/D File>Open 的"打开"对话框首个 Edit 填 `.out` 全路径回车;打印前断言框架标题含 `bias.out`(File>Print 打印的是**活动子窗口**)。注意 View→Output File 打开的是当前 dat 对应的 out,不是 bias 的。
- **Capture 原理图打印**:必须先激活 MDI 子窗口 `/ - (SCHEMATIC1 : PAGE1)`。workbook 标签模式下 Window 菜单无文档列表、`WM_MDIACTIVATE`/`WM_MDIRESTORE` 都无效;**物理点击顶部标签条**(PAGE1 标签实测屏坐标 ≈(96,129),屏 1707x1067;ImageGrab 截图像素==屏幕像素,阅读工具显示的是放大图,读坐标要按比例折算)。
- **Capture 主线程会硬阻塞**(连 WM_GETTEXT 都挂,常因启动恢复对话框):任何 SendMessage 前用 ctypes `SendMessageTimeoutW(SMTO_ABORTIFHUNG, 3000)`;挂死后 `taskkill //F //T //IM Capture.exe` → 删 `EXP3.DSNlck` → 重启 opj → 自动弹"projects were not properly closed"恢复对话框,点"确定"(id=1)即可重载。
- 打印 PDF 内容务必用 pymupdf 渲染成图人工核验(曾打印过错误的活动窗口,PDF 大小都接近 148KB,不可凭大小判断)。

## 手册级波形复刻 + 空载实验 (2026-10-29 第二轮)
- **Probe 打印对话框有 "Plots to Print" 列表**(多选 ListBox, 控件 ID 1130):默认只选第一项,
  File→Print 永远打最早开的窗口!必须 `LB_SETSEL(0x0185, 1, index)` 选中目标
  (LB_SETCURSEL 在多选列表只给焦点不设选中态),再发
  `WM_COMMAND, MAKEWPARAM(1130, LBN_SELCHANGE=1), hlb` 通知;否则 OK 报
  "At least one plot window must be selected"。
- **Probe 标注 (Plot→Label→Text, 命令 ID 0x802e)**:OK 后若状态栏出现
  "Move the text in the desired location" = 标签跟随鼠标,**必须物理点击放置;
  这种方式放置的标签才会进入打印输出**(直接自放置的可能不进打印)。标签锚定在
  数据坐标,Axis Settings 改量程后会"消失"(锚点移出可视区),与屏幕所见无关。
- **Agent 端口**:agent 默认连 5177(仅当启动 Capture 的进程环境有 ORCAD_MCP_PORT 才改);
  ZCode 注册的 orcad-capture MCP server 常驻 5177 且 agent 自动连上——**直接用
  mcp__orcad-capture__tcl_eval 等工具,不要自己再起 bridge**(10048 端口占用即它)。
- **TCL eval 前置条件**:GetActivePage 等需要 SchematicView——先物理点击 PAGE1
  workbook 标签(实测屏 (96,129), 屏 1707x1067)。
- **DBO 建网络别名**:`$wire NewAlias $st (MakeCString name) (MakeCPoint x y) (MakeLOGFONT) 0 $::DboValue_DEFAULT_OBJECT_COLOR`;
  枚举别名 = 页 NewWiresIter → 每根线 NewAliasesIter;flat net 名单 =
  $::DboSession_s_pDboSession → NewDesignsIter → NewFlatNetsIter → GetName
  (自动名 N0xxxx = 无别名;CommentText 用 NewCommentGraphicsIter→GetDboCommentText→GetText/SetText)。
- **Capture "Start Page" 内嵌浏览器会周期性把窗口拉回前台/z 序顶端**——自动化前先
  点 Start Page 标签 + Ctrl+F4 关掉。两个都被 set_fore 设过 TOPMOST 的窗口
  (Capture/Probe)会互相压盖:把不参与交互的 SetWindowPos(HWND_NOTOPMOST=-2)。
- **Capture 视图渲染滞后于 DB**:DBO 改属性后 F5 才刷新,勿以屏幕判断 DB 状态。
- **psp_cmd 追加仿真**:手写 tran2.cir(.PRINT V[Vo1], RL=100meg)→ psp_cmd -r tran2.cir
  → Probe File→Open tran2.dat → Add Trace V(Vo1)。
- **表3.1 口径**:指导书 cursor 最大值 = 含首周期上冲的全局峰值(2.5mA 档:
  Vim=5.01mV/Vom=394.6mV/Vom'=766.4mV → Av=78.7/Av'=152.9/Ri=0.77k/Ro=1.88k);
  稳态末整周期口径 Vim=4.48/Vom=374.7(Av=83.7) 作为备用列出。
- MFC 属性页(Axis Settings)跨进程切 tab:物理点第一页给焦点 → 直发 WM_LBUTTONDOWN/UP
  到 tab 控件 → VK_RIGHT,TCM_GETCURFOCUS(0x132F) 验证;OK 只提交激活过的页——
  复现不稳定,失败就手工兜底。


### 穿符号检查判据修订 (2026-10-29 第四轮)

- 只保留**整体横穿**模式;“端点扎入”模式删除——真扎入必然让目标引脚悬空(悬空检查
  兜底),而合法的贴符并接线(基极-源极短接)和结点分割点会误报。另加 **≤15 单位
  短导线豁免**。
- **CommentGraphic 的 SetLocation 不动文字**:图注/文本的显示位置由显示属性持有,
  锚点 GetLocation 恒 (0,0),挪锚点无视觉效果。要动文字得改其显示属性位置(未做)。
  报告裁剪图改为**不含图注**(Word 排版另写图注,更规范)。
## 安静模式:自动化不抢前台 (2026-10-29, orcad_quiet.py)
用户要在自动化运行时同时用电脑 → 禁止一切前台操作。orcad-mcp/orcad_quiet.py 实现:
- **全消息驱动**:菜单 PostMessage、对话框按钮 BM_CLICK(SendMessage)、文本 WM_SETTEXT、
  列表 LB_SETSEL、保存=向 Save As 对话框发 WM_COMMAND IDOK(不按回车)。
- **禁用**:SetForegroundWindow、TOPMOST、keybd_event、mouse_event/物理点击。
- 打印前 WM_CLOSE 关其他 MDI 子窗口(弹保存提示自动点"否");打印后用 pymupdf 读
  PDF 文本核验 Profile/标注,失手自动重试一次。
- **标注不用 Probe 内置 move-mode**(其放置点读真实光标 GetCursorPos,消息点击无效)——
  安静模式用 pymupdf 在打印出的 PDF 上叠写标注(insert_text + china-s 字体,
  图题 30%W/签名 62%W @14%H),波形本体仍是软件原打印。
- 实测:全流程(开关窗/加轨迹/打印/标注)零前台干扰,PDF 内容核验通过。
- **要物理点击的流程(PlaceWire 画线、Probe 内标注)放到 RDP 回环会话或错峰执行**:
  RDP 断开后 SendInput 仍在会话内有效(需 Win 专业版或 rdpwrap);
  或用 ZCode 闲时任务把整批 OrCAD 操作排到用户离开时跑。

## v5 实战补充(2026-10-29 第6轮,全消息驱动冷启动→切页→打印)

工具:`cap_open.py`(冷启动+恢复框)、`cap_activate.py`(切页)、`quiet_print.py`
(任意窗口打印)、`orcad_quiet.py --dat ...`(Probe 全流程 CLI)。

### 冷启动与端口

- `subprocess.Popen([Capture.exe, opj])` **必须传 `env`**,且 `ORCAD_MCP_PORT`
  要在 `import bridge` 之前设置。否则 agent 连默认 5177,本地 bridge 监听 5178,
  `bridge.BRIDGE.session()` 永远超时(实测 180s 超时)。
- 启动后可能出现两类模态框:
  - 标题 `OrCAD Capture CIS`,按钮只有 **确定/取消** = 上次异常关闭提示。
    点**确定**(id=1)才会加载工程;不点则停在 Start Page。
  - 标题带 ORCAP-1680、按钮 **是/否** = 是否恢复未保存修改。按需选否。
- 恢复框处理后 MDI 活动子窗口应是 `/ - (SCHEMATIC1 : PAGE1)`;若仍是 Start Page,
  说明工程没加载(检查是否点了取消)。

### 页面激活(替代物理点标签)

- `SelectPMItem {PAGE1}` 只把项目树节点选中,`GetActivePage` 仍报
  `Command Requires SchematicView`。
- 正确做法:向 `SysTreeView32` 子窗口依次 `PostMessage`:
  `WM_SETFOCUS` → `WM_KEYDOWN VK_RETURN` → `WM_KEYUP VK_RETURN`。
  实测一次成功,`GetActivePage` 返回 `_xxx_p_DboPage`,标题变为
  `... [/ - (SCHEMATIC1 : PAGE1)]`,**零前台/零鼠标**。
- 该法比 v4 记录的"物理点击 workbook 标签 (96,129)"更稳,优先使用。

### NewPlacedInst 正确签名(复制现有元件)

```tcl
set dev [$srcInst GetDevice $st]          ;# 必须是 DboDevice*,传字符串报 No matching function
set sess [$pg GetSession $st]
set lib  [$sess GetLib [CStr "C:/OrCAD/.../analog.olb"] $st]
set part [$lib GetPart [CStr "R.Normal"] $st]
set inst [$pg NewPlacedInst $st [CStr "RL"] [CStr "R"] $part $dev $loc $rot]
```

- **PackageName 传基名 `R`**;传 `R.Normal` 会变成 `R.Normal.Normal`,
  `GetSourcePartName` 返回 `R.Normal.Normal`,渲染异常(竖排文本的诱因之一)。
- 6 参调用 = 库默认方向;7 参带 `$rot` 会**连位号/值文本一起转**。
- 新件位号先成 `R?`,再 `SetEffectivePropStringValue("Reference","RL")` 改名。
- `device` 用 `$existingInst GetDevice $st` 借同类型元件的 DboDevice*;
  `GetPart` 的件名要带 `.Normal`。

### 保存

- `Menu "File::Save"` 会崩(结构修改已全走原生事务也崩)。
- 可靠路径:DB 改完 → `$pg MarkModified` → 让 Capture 前台 → **Ctrl+S**。
  标题无 `*` 不代表已保存,以 `.DSN` mtime 为准。
- 崩溃后 `.opj` 可能被降级(丢 Design Resources/schematic Doc),工程树空白;
  `git checkout -- exp3.opj` 恢复。

### 文本竖排(已知未解决)

- 复制 Rb1 新建 RL 后,RL 的位号/值文本竖排。DB 检查:`GetRotation`、
  `NewDisplayPropsIter` 的 rotation/location 与 Rb1 完全一致。
- 已试无效:重放新件、prop `SetRotation` 0/1/2/3、
  `ResetAllDisplayPropertiesFontToDefault`、改 PackageName、换 6/7 参。
- `SetFont(LOGFONT)` 直接崩 Capture。**暂时接受**,不要为它反复重做设计。

### 编码 / 提权 / DPI / IME

- PowerShell `Set-Content -Encoding UTF8` 写 **BOM**;Tcl 报
  `invalid command name "\ufeffset"`。读 `.tcl` 用 `utf-8-sig`,或写 ASCII。
- 前台是管理员窗口时,中完整性进程的 `SetCursorPos`/`SetForegroundWindow`
  返回 0;需要物理输入时用 `Start-Process pythonw -Verb RunAs` 跑 `elev_run.py`。
- 非 DPI 感知进程的坐标 = 物理像素 / 1.5;物理点击前先确认 DPI 缩放。
- 中文输入法会吞字母快捷键;发按键前先 Shift 切英文。

### 安静打印一条命令

```bat
python quiet_print.py "OrCAD Capture" out_sch.pdf
python quiet_print.py "PSpice A/D"    out_bias.pdf
python orcad_quiet.py --dat tran.dat --out out_tran.pdf ^
  --traces V(Vs) V(Vi) V(Vo) --caption "..." --name "信255 王保哲" --two-frame
```

- 三者都是 File>Print(PostMessage WM_COMMAND)→ 打印框默认按钮 `BM_CLICK`
  → Save As 首个可见 Edit `WM_SETTEXT` → 对话框 `WM_COMMAND IDOK`。
- 打印前目标文档必须已打开并处于活动子窗口;Capture 还要先 `cap_activate.py`。
- 打完必须 pymupdf 读文本/渲染核验(大小相近不能证明内容对)。

## 原理图"重构后核验"铁律 (2026-10-29 实验4 地线重构)

- **批量 PlaceWire 脚本中断 = 静默半成品**。实验4 重构脚本在 PAGE3/4/5 各只放了一部分
  导线就断了(异常/超时),页面看起来"差不多对",实际 GND 悬空、返回线断开。低分辨率
  整页截图**看不出来**——红点/断口只有放大才可见。
- **核验方法(必须做,替代目测)**:重构完成后重新 dump 每页导线端点清单
  (`NewWiresIter` → `GetStartPoint/GetEndPoint/GetId`),对拓扑应相同的页面逐段比对
  (实验4 的 PAGE2~5 均应为同一份 14 段清单)。再打印 PDF 后用 pymupdf 150dpi 放大
  渲染接线区确认:无悬空红点、GND 符号贴线、回路闭合。
- **坐标骨架(实验4 共源放大器,单位 0.01inch,按手册图4.15 实测比例,M2 锚定 (600,380))**:
  M2 栅(590,400) 漏(620,380) 源(620,420) 衬(630,430),**衬底在符号旁短接源极引线**
  ((630,430)-(620,430) + 结点 (620,430),源极单线下地——手册无独立衬底回线);
  R1(610,286) 引脚 (620,276)/(620,316) → (620,380) 直落;顶轨 y=248(R1 顶上方 28),
  右到 V1 列 x=810;V1(800,292) 引脚 (810,292)/(810,332),V1− 直落 (810,536);
  底轨 y=536;V2(390,488)/V3(390,498) 引脚 (400,488)/(400,528),竖引线
  (400,400)-(400,488) 88 高,底 (400,528)-(400,536) 8 矮脚;GND(620,536) 挂母线。
  **每页 12~13 根导线(PlaceWire 分段数可能不同),以端点清单拓扑比对为准**。
  比例出处:以 M2 本体高 40 为标尺量手册图4.15——顶轨距 R1 顶 36、V1 与 R1 同带、
  V2 中心在栅线下 108/母线上 28、源极下引 116、V1− 下引 204、V2 列距 M2 218、
  V1 列距 M2 194。改布局先量手册再算坐标,不要凭感觉挪。
- 打印/核验分工:GUI 连通性错误只影响原理图 PDF;若仿真数据来自自包含 .cir
  (psp_cmd 复跑),页面断线不影响已交付数据——先修图,不必重跑仿真。

## 卡顿与意外弹窗:硬超时与自动恢复 (2026-10-29, capture_guard.py)

**"卡很久"只有四类根因**,全部有对策,不要每次重新猜:
(a) 模态对话框饿死 agent 定时器 → 每次 eval 白等 30s 超时,脚本里连环 eval 就是连环卡;
(b) 主窗口真假死(IsHungAppWindow 为真)→ 任何 SendMessage 都无响应,消息路径已失效;
(c) 僵尸 Capture 进程/残留 .DSNlck → 下一次自动化连错对象或带病打开;
(d) 保存被弹窗/死锁挡住 → 脚本不知情继续跑,错误滞后爆发。

### 四个原语(所有长流程改用,别再裸写)

- `capture_guard.eval_safe(s, tcl, timeout=20, retries=2)`:超时→reap→重试;
  agent disconnected→等 4s 自愈重连再试;**TCL error 立即抛**(确定性脚本错误,
  重试只会 20s×N 浪费)。彻底失败时异常里带残余弹窗清单和恢复阶梯。
- `capture_guard.reap(expected=EXPECTED_TITLES, dry=False)`:枚举 Capture pid 名下
  可见 #32770,按语义表点按钮。打印/另存为/打开等**流程预期弹窗永远跳过**
  (点错毁掉进行中的流程);收割不动的残弹窗会在 eval_safe 失败诊断里列出。
- `capture_guard.save_verified(s, dsn_path)`:File::Save(带弹窗恢复)→ 轮询
  .DSN mtime(settle=10s)。返回 'saved'/'no-change'(无修改可存,非故障);
  mtime 不动且存在弹窗时抛诊断(另存为=设计未命名,需流程显式给路径)。
- `capture_guard.health(opj=None)`:一屏体检——主窗口/假死/僵尸/弹窗/残留锁
  (锁在 Capture 运行中=正常)/agent ping。CLI: `python capture_guard.py health <dsn>`。

### reap 语义表(历史实证)

| 弹窗特征 | 自动动作 |
|---|---|
| 标题含 ORCAP-1680(是/否) | 点**否**(加载磁盘态,不恢复未保存修改) |
| 上次异常关闭提示(确定/取消) | 点**确定**(加载磁盘态;取消会留在 Start Page) |
| Save changes / 保存更改 | 默认点**是**(保住已改内容;故意丢弃时传 save_changes=False) |
| 崩溃报告/已停止工作 | 点**关闭** |
| 其余未知 | 点 IDOK(1),无则第一个按钮;全部记录到返回值 |
| 标题命中 EXPECTED_TITLES | **不动**(那是打印/另存为/打开等流程自己的弹窗) |

### 实践守则

- 裸 `s.eval` 只允许出现在一行式试探里;任何循环/批量流程必须 eval_safe。
- 每个等待都要有 deadline + 升级路径(reap→health→taskkill+删锁+cap_open.py),
  禁止无上限 while 轮询;eval 单次 ≤20s(默认),不要为了"保险"调到 60s——
  那正是卡顿时长的来源。
- 批量操作(重构/多页打印)前跑一次 `health(dsn)`;结束后再跑一次确认无残留。
- BM_CLICK 一律走 SendMessageTimeoutW(SMTO_ABORTIFHUNG, 3s)——对可能假死的窗口
  裸 SendMessage 会把自己也挂死(capture_guard._msg 已封装)。
- 僵尸判定 = exe_pids() − capture_pids()(有映像无窗口);tasklist 慢,只在 health 用。

## 连通性裁决标准:引脚级审计 (2026-10-29, sch_connectivity_audit.py)

- **目视与放大 PDF 核验都有盲区**。实验4 实证:V1(5V) 负极悬空,红竖线贴着电池符号,
  两轮 150dpi 放大核验都把它误读为符号自身图形;用户目视反而发现了。
- **画完/改完原理图必跑** `python sch_connectivity_audit.py PAGE1 ...`:
  dump 引脚热点(GetOffsetHotSpot)+导线端点+结点 → 并查集 → 报告
  悬空引脚(按宿主元件位置)/T-TOUCH无结点(端点落另一根线中间且无结点=电气断开)/
  十字交叉(提示,不连通)。
- 判据细节(踩过的坑):
  - 引脚列表被逗号拍平:解析时按数字两两成对还原;
  - **悬空判定是 `p not in ep_map and find(p)==p`**,不是 `find(p)==p`——
    引脚坐标恰好是连通组树根时后者误报(导线 END 点常成为根);
  - 端点-端点/端点-引脚同坐标即连通,无需结点对象;结点只影响 T 触与显示。
- 结点 API 勘误:DboPage **没有 NewJunctionsIter**(appendixB 手册写错类);
  用 `IsConnectionPoint(point,status)`/`NewObjectsAtPointIter`(迭代器方法是
  Next/GetKey/GetType,不是 GetFirstOf)。补圆点用 agent 命令 `PlaceJunction x y`(英寸),
  实测有效——多线汇聚点没有圆点时,视觉上分不清"相连"与"交叉"。
- 典型漏接线模式:**电源符号的负极**。画了 V1+→负载轨就以为回路闭合,
  返回路径(V1−→地)最容易漏;审计会直接点名"元件@(690,140) 引脚@(700,180) 悬空"。

## 按手册图复刻布局的实证补充 (2026-10-29 第二轮)

- **SetLocation 签名分家**:`DboPartInst`/`DboGlobal`(DboNetSymbolInstance 系)的
  `SetLocation(location)` **不带 status**;带 `$_st` 报 "Wrong # args"。
  DboPlacedInst 的带 status(以实测为准,错了看报错参数个数)。
- **PlaceWire 会自动分段**:走线跨越其它导线端点/结点时被拆成多段
  (如 (620,470)-(700,470) 经 (650,470) 分两段)。删线必须先 dump 现状拿真实端点,
  不能凭"我放过的坐标"猜。
- **圆点是自动的**:≥3 条线/引脚汇聚 Capture 自动渲染连接圆点,不需要 junction
  对象;**T 型接入(端点落在另一根线中间)才必须 PlaceJunction**(电气需要,
  非显示)。PlaceJunction 在已有自动圆点的点可能静默不建对象——无害。
- **Tcl 8.4 expr 没有 min/max**(8.5 才有),用三元 `? :` 替代。
- **结点探测正道**:`DboWire.PointIsJunction(point,status)`(DboWire 还有
  `RemoveExtraJunctions`/`JunctionOnWire`);页面级没有可用的 junction 枚举
  (NewJunctionsIter 不存在,NewObjectsAtPointIter 只返回端点对象)。
- **移动元件带位号/值文本一起走**,已放置元件平移安全;值类操作无崩溃风险。
- 对照手册图复核时,先比"拓扑骨架"(同轴/直落/母线拉通/地挂母线)再比标签位置;
  交付前跑 `sch_connectivity_audit.py` + 渲染对照,两道闸都过才算完。

### 符号引脚几何与"穿符号"检查 (2026-10-29 第三轮)

- **不同符号的引脚偏移不同,必须 dump 实测,绝不能假设**。实验4 实证:
  VDC 电池引脚 = loc+(10,0)/(10,40);VSIN 圆源引脚 = loc+(10,-10)/(10,30)。
  按 VDC 的几何给 VSIN 页定母线高度 → 母线端点扎在圆符号半腰,底部接线变成
  穿符号的隐藏短线(电气通,视觉完全错,用户一眼抓住)。
- **电源符号标准位**(共源/共射放大器左侧):顶部引脚距栅极线 20、底部引脚距
  母线 10。V2→(260,420)/V3→(260,430),引脚统一 (270,420)/(270,460),
  上引 (270,420)-(270,400),下引 (270,460)-(270,470)。
- **审计新增穿符号检查**(sch_connectivity_audit.py 已内置):判据 = 导线端点
  落在"引脚包络核"(pins bbox ±5)内且不是引脚,或导线整体横穿核。
  **不要用 GetBoundingBox 做这个判据**——它把显示属性文本(值标签/属性块)也
  包进包围盒,贴标签的导线全部误报。
- API:GetBoundingBox() **无参数**返回 CRect,用 DboTclHelper_sGetCRectTopLeft/
  sGetCRectBottomRight 解包。
- 三道闸缺一不可:引脚级电气审计(悬空/T触)+ 穿符号几何审计 + PDF 渲染对照。
  前两道机器把关,渲染对照只看机器查不到的观感(比例/标签位置)。

### 报告用图: 从打印 PDF 裁电路特写 (2026-10-29, crop_report_figure.py)

- 手册书里的"原理图插图" = 标准图纸裁掉图框的样子。报告排版用**裁剪 PNG**,
  整页 PDF 留作软件打印证据。
- 裁剪定位:电路 = **饱和色描线**(max-min 通道差>0.2)的并集——边框/网格/标题栏
  是黑/灰线自动排除;属性文本取电路周边 30pt 内的词;图注按"图4.x"所在行带、
  x<460 的词(防止并进右侧标题栏文本)。
- **标题栏与电路横向重叠**(V1 右缘 ~591pt > 标题栏左缘 ~573pt),含图注的矩形
  必然带到标题栏一角 → 渲染后白覆盖"电路底缘以下、图注右侧"的右下矩形。
  注意 pymupdf 的 text blocks 会把图注与标题栏文本合并成横跨整页的 block,
  必须用 words 级处理。
- GetBoundingBox 含显示属性文本,同样不适合做定位。

## 实战实例:按手册图复刻全页重排 (2026-10-29 第四轮, examples/exp4_mos/relayout_fig415.py)

完整案例脚本:`examples/exp4_mos/relayout_fig415.py` —— 量手册 → 坐标表 → 删/移/布线
→ 结点 → save_verified,四步全部参数化。换电路/换手册图时只改 DEL/WIRE/MOVES 三张表。

**工作流(重排任何"与手册不一致"的页面都按这个顺序):**
1. **量手册**:以已知尺寸的元件为标尺(M2 本体高 40),量出所有间距×换算系数
   (标尺实际单位/标尺像素)。改布局先量手册再算坐标,不要凭感觉挪。
2. **列坐标表**:锚定一个元件不动,其余由间距推出;注意各符号引脚偏移不同
   (VDC/V3 已实测记录在上),引脚位置 = loc + 偏移。
3. **删旧线**:端点匹配(FIND_DEL 模板)→ SelectObjectById → Menu "Edit::Delete"。
   全删后旧结点属性随导线一起消失,无需单独删结点。
4. **移件/GND**:SetLocation 不带 status。
5. **布新线**:PlaceWire(英寸,y 向下);跨越其它线端点会被自动分段——最终以
   重新 dump 的端点清单为准,不要以"我放了什么"为准。
6. **结点**:只有"端点落在另一根线中间"的 T 点才 PlaceJunction;≥3 线端点相接
   自动画圆点。
7. **闸门**:save_verified(mtime)→ sch_connectivity_audit(悬空/横穿/T触)→
   打印 PDF → crop_report_figure.py 报告特写图。

本案例的两个特殊点:
- **基极-源极并接**:手册要求基极与源极同一条线入地 → 符号旁 10 单位短接线 +
  T 点结点 (620,430),源极单线下地;不做独立衬底回线。
- **图注挪不动**:CommentGraphic 的 SetLocation 无视觉效果(位置在显示属性里,
  锚点恒 (0,0));报告特写图不含图注,由 Word 排版另写。

## 从零画整页原理图 (2026-10-30 实验5 差分放大, ex5-example)

- NewPlacedInst 直接从库件建实例(无需已有同类型元件):
  $pg NewPlacedInst $st [CStr ref] [CStr $part] $symbol $dev [CPoint 0 0] $rotation,
  其中 $symbol = $lib GetPart [CStr "$part.Normal"],$dev = [[$symbol GetPackagePtr] GetDevice 0 $st]。
  与复制现有实例的 $dstPage NewPlacedInst $srcInst $st [CPoint] 是两个不同签名。
- 锚点定位:先 dump 引脚(NewPinsIter→GetPinName+GetOffsetHotSpot),按锚点引脚
  或引脚均值算偏移,SetLocation (x-ax) (y-ay) 把锚点精确放到目标坐标。
- 镜像:$inst SetMirror $mirror(差分对左右对称件用)。
- 引脚名大小写按符号实测:Q2N2222 是小写 b/c/e,按 B 找锚点直接报 not found。
- SetPageWidth/SetPageHeight 单位是 doc(0.01inch):Letter = 11000/8500。
  旧记录 SetPageWidth 1100/850 得到的 doc=110×85(0.1页)——是错的,以 08 脚本实测为准
  (BEFORE 1100,850→doc 110,85;AFTER 11000,8500→doc 1100,850,重开保持)。
- 地符号(Globals)锚点是热点不是 loc:PlaceGround 后 GetOffsetHotSpot 比 loc 偏
  (+10,0),SetLocation (x-10) y 才让热点落在导线端点上;挂接成功判据 =
  $g GetWire $st 返回非 NULL(=NULL 即悬空,别只看坐标)。
- 核对顺序:CloseProject → Open opj → OPage → 重读 GetPartInstCount/GetWireCount/
  GetPageWidth(重开后计数与页面尺寸不变才算落盘);打印 PDF→pymupdf 渲染对照手册图。
- 本例工程 D:/Users/Document/OrCAD/auto/ex5-example/:编号 tcl 脚本(01~23 逐步演进)+
  verification/session.jsonl(每步脚本/结果/错误留档)+ 最终 PDF/PNG 对照 reference-fig5-4.png。
  新电路从零画页可整流程照抄。
