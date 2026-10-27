"""Extract the OrCAD Capture Tcl/Tk Extensions manual into searchable text files.

官方手册 PDF 随 OrCAD 安装附带(通常位于
<OrCAD>\\tools\\capture\\tclscripts\\OrCAD_Capture_TclTk_Extensions.pdf)。
本脚本将其全文提取到 docs/,供 orcad-mcp 的 `tcl_api_search` 工具检索。

用法:
    python tools/extract_manual.py                # 使用默认安装路径
    python tools/extract_manual.py <pdf路径> <输出目录>
需要: pip install pypdf
"""
import os
import re
import sys

DEFAULT_PDF = (r"C:\OrCAD\OrCAD_16.6_Lite\tools\capture\tclscripts"
               r"\OrCAD_Capture_TclTk_Extensions.pdf")
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

# 手册章节 → 输出文件(附录 A/B/C 是全部命令清单,章节是工作流教程)
SECTIONS = [
    ("sec_autoload_p13-16.txt", 13, 16),      # 自动加载机制
    ("sec_dbapi_p29-42.txt", 29, 42),         # 数据库 API 遍历/属性
    ("sec_commserver_p102-105.txt", 102, 105),  # 通信服务器
    ("sec_pdfexport_p86-99.txt", 86, 99),     # PDF 导出
    ("appendixA_capture_commands.txt", 113, 146),  # 用户操作命令全集
    ("appendixB_database_commands.txt", 147, 825),  # Dbo 数据库命令全集
    ("appendixC_cis_commands.txt", 826, 922),  # CIS 命令
]


def main() -> int:
    pdf = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    outdir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    from pypdf import PdfReader
    r = PdfReader(pdf)
    os.makedirs(outdir, exist_ok=True)
    full = os.path.join(outdir, "OrCAD_Capture_TclTk_Extensions_fulltext.txt")
    with open(full, "w", encoding="utf-8") as f:
        for i, p in enumerate(r.pages):
            f.write(f"\n===== PAGE {i + 1} =====\n{p.extract_text() or ''}\n")
    txt = open(full, encoding="utf-8").read()
    pat = re.compile(r"===== PAGE (\d+) =====\n(.*?)\n(?====== PAGE )", re.S)
    for fname, a, b in SECTIONS:
        body = "\n".join(m.group(2) for m in pat.finditer(txt) if a <= int(m.group(1)) <= b)
        with open(os.path.join(outdir, fname), "w", encoding="utf-8") as f:
            f.write(body)
    print(f"extracted {len(r.pages)} pages -> {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
