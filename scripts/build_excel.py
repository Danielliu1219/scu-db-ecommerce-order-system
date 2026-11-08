# -*- coding: utf-8 -*-
"""生成《软件功能清单.xlsx》以及用于 Word 截图的两张打印页。"""

from __future__ import annotations

import argparse
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break

from data import BUSINESS_RULES, PROJECT, FUNCTIONS, SQL_TASKS, TABLES

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "deliverables"

# ---------- 样式常量 ----------
NAVY = "1F3864"
BLUE = "2E5C8A"
LIGHT_BLUE = "EAF0F8"
PALE_BLUE = "F7F9FC"
BORDER_BLUE = "B4C6E7"
GRAY = "595959"
WHITE = "FFFFFF"

THIN = Side(style="thin", color=BORDER_BLUE)
MEDIUM = Side(style="medium", color=NAVY)
ALL_BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

TITLE_FONT = Font(name="微软雅黑", size=16, bold=True, color=WHITE)
META_FONT = Font(name="宋体", size=9, color=GRAY)
HEADER_FONT = Font(name="微软雅黑", size=9, bold=True, color=WHITE)
BODY_FONT = Font(name="宋体", size=8.2, color="222222")
BODY_BOLD = Font(name="宋体", size=8.2, bold=True, color=NAVY)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
LEFT_TOP = Alignment(horizontal="left", vertical="top", wrap_text=True)


def _title_block(ws, title: str, subtitle: str, last_col: int) -> None:
    """写入标题行与元信息行。"""
    last = get_column_letter(last_col)
    ws.merge_cells(f"A1:{last}1")
    c = ws["A1"]
    c.value = title
    c.font = TITLE_FONT
    c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = CENTER
    ws.row_dimensions[1].height = 34

    ws.merge_cells(f"A2:{last}2")
    c = ws["A2"]
    c.value = subtitle
    c.font = META_FONT
    c.fill = PatternFill("solid", fgColor=LIGHT_BLUE)
    c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)
    c.border = Border(bottom=Side(style="thin", color=BORDER_BLUE))
    ws.row_dimensions[2].height = 22


def _header_row(ws, row: int, headers: list[str]) -> None:
    for col, text in enumerate(headers, start=1):
        c = ws.cell(row=row, column=col, value=text)
        c.font = HEADER_FONT
        c.fill = PatternFill("solid", fgColor=BLUE)
        c.alignment = CENTER
        c.border = Border(left=THIN, right=THIN, top=MEDIUM, bottom=MEDIUM)
    ws.row_dimensions[row].height = 30


def _body_row(ws, row: int, values: list[str], heights: float = 88) -> None:
    for col, text in enumerate(values, start=1):
        c = ws.cell(row=row, column=col, value=text)
        c.font = BODY_BOLD if col == 2 else BODY_FONT
        c.alignment = CENTER if col in (1, 3, 7) else LEFT
        c.border = ALL_BORDER
        c.fill = PatternFill("solid", fgColor=PALE_BLUE if row % 2 == 0 else WHITE)
    ws.row_dimensions[row].height = heights


def _set_widths(ws, widths: dict[str, float]) -> None:
    for col, width in widths.items():
        ws.column_dimensions[col].width = width


def _page_setup(ws, print_area: str, landscape: bool = True) -> None:
    ws.sheet_view.showGridLines = False
    ws.print_options.horizontalCentered = True
    ws.print_options.verticalCentered = False
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.paperSize = 9  # A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = print_area
    ws.page_margins.left = 0.31
    ws.page_margins.right = 0.31
    ws.page_margins.top = 0.30
    ws.page_margins.bottom = 0.30
    ws.page_margins.header = 0.15
    ws.page_margins.footer = 0.15
    ws.oddHeader.left.text = ""
    ws.oddHeader.center.text = ""
    ws.oddHeader.right.text = ""
    ws.oddFooter.left.text = ""
    ws.oddFooter.center.text = ""
    ws.oddFooter.right.text = ""
    ws.print_options.gridLines = False


def _function_values(fn: dict) -> list[str]:
    return [
        fn["id"],
        fn["name"],
        fn["role"],
        fn["desc"],
        fn["constraints"],
        f"【输入】{fn['input']}\n【处理】{fn['process']}\n【输出】{fn['output']}",
        fn["tables"],
    ]


def _build_function_sheet(ws, title: str, functions: list[dict], print_area: str) -> None:
    headers = ["功能编号", "功能名称", "使用角色", "功能描述", "约束条件与异常处理", "输入 / 处理 / 输出", "主要数据表"]
    _title_block(
        ws,
        title,
        f"项目：{PROJECT['name']}（{PROJECT['scheme']}）    组号：第 {PROJECT['group_no']} 组    "
        f"版本：{PROJECT['version']}    日期：{PROJECT['date']}",
        len(headers),
    )
    _header_row(ws, 3, headers)
    for idx, fn in enumerate(functions, start=4):
        _body_row(ws, idx, _function_values(fn), heights=88)
    _set_widths(ws, {"A": 9.0, "B": 14.5, "C": 12.0, "D": 32.5, "E": 34.5, "F": 27.5, "G": 15.0})
    _page_setup(ws, print_area)


def build_workbook(group_no: str = "X", path: Path | None = None) -> Path:
    PROJECT["group_no"] = group_no
    path = path or OUT_DIR / "软件功能清单.xlsx"
    path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    wb.properties.title = f"{PROJECT['name']}功能清单"
    wb.properties.subject = "数据库系统原理课程设计——功能清单"
    wb.properties.creator = f"第 {group_no} 组"
    wb.properties.keywords = "电商订单管理系统, 功能清单, 数据库课程设计"

    # 1) 完整可编辑清单
    ws = wb.active
    ws.title = "功能清单"
    _build_function_sheet(ws, f"{PROJECT['name']}功能清单", FUNCTIONS, "A1:G12")
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = "A3:G12"
    ws.print_title_rows = "1:3"
    # 完整清单若打印，按宽度缩放，纵向自动分页
    ws.page_setup.fitToHeight = 0

    # 2) 打印页 1：FR-01 ~ FR-04
    ws1 = wb.create_sheet("打印1")
    _build_function_sheet(ws1, f"{PROJECT['name']}功能清单（1/2）", FUNCTIONS[:4], "A1:G8")

    # 3) 打印页 2：FR-05 ~ FR-09
    ws2 = wb.create_sheet("打印2")
    _build_function_sheet(ws2, f"{PROJECT['name']}功能清单（2/2）", FUNCTIONS[4:], "A1:G9")

    # 4) 核心数据表
    ws3 = wb.create_sheet("核心数据表")
    headers = ["序号", "表名", "中文名", "关键字段", "作用"]
    _title_block(ws3, f"{PROJECT['name']}核心数据表规划", "共 11 张表；所有表使用 InnoDB、utf8mb4，金额使用 DECIMAL(10,2)，时间使用 DATETIME。", 5)
    _header_row(ws3, 3, headers)
    for i, table in enumerate(TABLES, start=4):
        vals = [table["no"], table["name"], table["cn"], table["fields"], table["purpose"]]
        for col, text in enumerate(vals, start=1):
            c = ws3.cell(row=i, column=col, value=text)
            c.font = BODY_BOLD if col == 2 else BODY_FONT
            c.alignment = CENTER if col in (1, 2, 3) else LEFT
            c.border = ALL_BORDER
            c.fill = PatternFill("solid", fgColor=PALE_BLUE if i % 2 == 0 else WHITE)
        ws3.row_dimensions[i].height = 40
    _set_widths(ws3, {"A": 5.5, "B": 15.5, "C": 13.5, "D": 70, "E": 26})
    _page_setup(ws3, "A1:E15")

    # 5) SQL 任务
    ws4 = wb.create_sheet("SQL任务")
    headers = ["编号", "任务", "涉及表", "主要 SQL 技术"]
    _title_block(ws4, f"{PROJECT['name']}SQL 任务规划", "课程要求的 4 项 SQL 任务 + 2 项扩展统计任务。", 4)
    _header_row(ws4, 3, headers)
    for i, task in enumerate(SQL_TASKS, start=4):
        vals = [task["id"], task["task"], task["tables"], task["techniques"]]
        for col, text in enumerate(vals, start=1):
            c = ws4.cell(row=i, column=col, value=text)
            c.font = BODY_BOLD if col == 2 else BODY_FONT
            c.alignment = CENTER if col == 1 else LEFT
            c.border = ALL_BORDER
            c.fill = PatternFill("solid", fgColor=PALE_BLUE if i % 2 == 0 else WHITE)
        ws4.row_dimensions[i].height = 36
    _set_widths(ws4, {"A": 8, "B": 42, "C": 32, "D": 30})
    _page_setup(ws4, "A1:D10")

    # 6) 说明页
    ws5 = wb.create_sheet("说明")
    ws5.sheet_view.showGridLines = False
    _title_block(ws5, "使用说明", "本工作簿既是可编辑的功能清单，也是 Word 中功能清单截图的来源。", 4)
    notes = [
        ("1", "“功能清单”工作表包含全部 9 项功能，可直接编辑、筛选和打印。"),
        ("2", "“打印1”“打印2”工作表分别容纳 4 项和 5 项功能，用于导出 Word 中的两张高清表格图。"),
        ("3", "“核心数据表”和“SQL任务”工作表是数据库设计与后续实现的参考，不随 Word 功能清单截图展示。"),
        ("4", "字段口径：功能编号、功能名称、使用角色、功能描述、约束条件与异常处理、输入/处理/输出、主要数据表。"),
        ("5", "修改 scripts/data.py 后运行 python scripts/build_deliverables.py，可同时刷新 Excel、Word 与 Markdown 文档。"),
    ]
    for i, (no, text) in enumerate(notes, start=4):
        ws5.cell(row=i, column=1, value=no).font = BODY_BOLD
        ws5.cell(row=i, column=1).alignment = CENTER
        ws5.merge_cells(start_row=i, start_column=2, end_row=i, end_column=4)
        c = ws5.cell(row=i, column=2, value=text)
        c.font = BODY_FONT
        c.alignment = LEFT
        for col in range(1, 5):
            ws5.cell(row=i, column=col).border = ALL_BORDER
        ws5.row_dimensions[i].height = 40
    _set_widths(ws5, {"A": 6, "B": 50, "C": 20, "D": 20})
    _page_setup(ws5, "A1:D9")

    wb.save(path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", default="X")
    args = parser.parse_args()
    print(build_workbook(args.group))
