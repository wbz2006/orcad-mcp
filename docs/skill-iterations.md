# skill-iterations.md — orcad-automate skill 迭代日志

目标:以"新会话只靠 skill 文件重做任务"的标准,对实验3剩余任务做 5 轮完整迭代;
每轮 = 真实任务执行 + 坑记录 + skill 文件改进(SKILL.md / references/api-notes.md /
examples/probe_export.py)。

| 轮次 | 任务 | 新坑/缺口 | skill 改进 |
|---|---|---|---|
| 1 | IC=2mA 全列(Rb1=73k,Vs=10.5mV;图3.21~3.24 四张图+表3.1 行) | ①Probe 打印对话框 Plots to Print 多项时选择不可靠→**打印前关掉其他 dat 窗口(Ctrl+F6 循环+Ctrl+F4),单窗口确定**;②标签放置点击被 Capture 抢前台→标签停在未放置态不进打印,**放置点击前重新置顶+前台化**(probe_label_move_mode 加固);③TCL 需 SchematicView→SelectPMItem{PAGE1}+工程树回车比 workbook 标签点击可靠;④DBO 改属性后 F5 才刷新视图 | probe_export.py v1(参数化一站式导出)+tcl/prep_ic_loaded.tcl(参数化 IC 档切换) |
| 2 | IC=3mA 全列(Rb1=45k,Vs=12.5mV;图3.21b~3.24b 四张图+表3.1 行) | ①流程已脚本化后一轮仅需 8 次工具调用(上轮 30+);②probe_export 一次成功,标注双落 0V 线;③教训复用:关窗单打印/选择 PM+回车/F5 刷新全部一次通过 | 无新增(验证 v1 脚本的泛化性:换参数直接复用) |
| 3 | 失真(1) Rb1=100k 去 Rs、Vs=30mV(图3.25~3.27) | **DBO 写删除类操作(DeleteWire/NewWireScalar/DeletePartInst)会破坏 DB 一致性→保存时 Capture 崩溃退出×2(含 ORCAP-1680 恢复询问+quit unexpectedly 报告框)**;结构性修改必须走原生事务:SelectObjectById <id>+Menu Edit::Delete、官方 PlaceWire(英寸);DBO 值类 SetEffectivePropStringValue/别名改名安全;psp_cmd 读 UTF-8 中文注释会乱码印进 PDF→.cir 注释一律 ASCII;崩溃恢复对话框有两类(确定/取消 与 是/否),都要处理;Probe 文本窗口打印对话框无 Plots 列表且 OK 位置不同,需按控件 dump 定位 | 原生事务手术配方+两类恢复对话框处理+.cir ASCII 规则 |
| 4 | 失真(2) Rb1=20k(图3.28~3.30) | 双窗口 Plots-to-Print 消息选择再次失败(LB_SETSEL+notify 仍打旧窗)→**铁律:打印前把 Probe 关到只剩目标窗口**(Ctrl+F6 循环+Ctrl+F4);文本窗口不进 Plots 列表;残留子窗口(bias7.out)会混在子窗口循环里,需逐个辨认标题;等待文件返回 bool,打印大小要用 os.path.getsize(路径) | 铁律入 api-notes;probe_export 标注函数已加固 |
| 5 | skill 整体审计:SKILL.md 重写至与实际流程一致 + HANDOFF.md 收口 | ①SKILL.md v1 停留在"matplotlib 出图"时代,与打印管线实战严重漂移→v2 重写;②AGENTS.md 三条硬约束被实证推翻(Probe 自动化已走通/lck 期值类 DBO 修改安全/图3.8 非半成品)→按证据更新;③HANDOFF.md 按 AGENTS.md 会话协议补写本轮条目 | SKILL.md v2 + AGENTS.md 约束修订 + HANDOFF 条目 + 记忆同步 |

状态:**5 轮迭代完成**(2026-10-29)。产出:IC=2mA/3mA 两档全列(8 张图)+ 失真观察 6 张图,
全部为软件自身打印导出并渲染核验;表3.1 三档齐全;skill 三件套(SKILL.md v2 /
api-notes.md / probe_export.py)+ 项目 AGENTS.md/HANDOFF.md 同步更新。
