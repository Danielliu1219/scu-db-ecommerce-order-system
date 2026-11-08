# -*- coding: utf-8 -*-
"""生成课程提交用 Word：《第X组_电商订单管理系统.docx》。"""

from __future__ import annotations

import argparse
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

from data import (
    BUSINESS_RULES,
    COURSE_MAPPING,
    DOC_SECTIONS,
    FLOW_STEPS,
    FUNCTIONS,
    PLAN,
    PROJECT,
    ROLES,
    SCOPE_IN,
    SCOPE_OUT,
    SQL_TASKS,
    TABLES,
    TECH_STACK,
)

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUT_DIR = ROOT / "deliverables"

FONT_BODY = "宋体"
FONT_HEAD = "黑体"
FONT_UI = "微软雅黑"
NAVY = RGBColor(0x1F, 0x38, 0x64)
BLUE = RGBColor(0x2E, 0x5C, 0x8A)
GRAY = RGBColor(0x59, 0x59, 0x59)
DARK = RGBColor(0x22, 0x22, 0x22)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NAVY_HEX = "1F3864"
BLUE_HEX = "2E5C8A"
LIGHT_BLUE_HEX = "EAF0F8"
PALE_BLUE_HEX = "F7F9FC"
BORDER_HEX = "B4C6E7"


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
def set_run_font(run, name: str = FONT_BODY, size: float = 10.5, bold: bool = False,
                 color: RGBColor | None = None, italic: bool = False) -> None:
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.get_or_add_rFonts()
    rfonts.set(qn("w:eastAsia"), name)
    rfonts.set(qn("w:ascii"), name)
    rfonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def shade_cell(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_margins(cell, top: float = 0.05, bottom: float = 0.05,
                     left: float = 0.12, right: float = 0.12) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = OxmlElement("w:tcMar")
    for side, value in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(int(value * 567)))
        el.set(qn("w:type"), "dxa")
        tc_mar.append(el)
    tc_pr.append(tc_mar)


def set_cell_border(cell, **kwargs) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_borders = tc_pr.find(qn("w:tcBorders"))
    if tc_borders is None:
        tc_borders = OxmlElement("w:tcBorders")
        tc_pr.append(tc_borders)
    for edge in ("top", "left", "bottom", "right"):
        if edge not in kwargs:
            continue
        edge_data = kwargs[edge]
        tag = f"w:{edge}"
        element = tc_borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            tc_borders.append(element)
        for key in ("sz", "val", "color", "space"):
            if key in edge_data:
                element.set(qn(f"w:{key}"), str(edge_data[key]))


def set_table_borders(table, color: str = BORDER_HEX, size: int = 4) -> None:
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        borders.append(el)
    tbl_pr.append(borders)


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_row_cant_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    cant_split.set(qn("w:val"), "true")
    tr_pr.append(cant_split)


def set_col_width(cell, width_cm: float) -> None:
    cell.width = Cm(width_cm)
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(int(width_cm * 567)))
    tc_w.set(qn("w:type"), "dxa")


def add_field(paragraph, code: str) -> None:
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = code
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_sep)
    run._r.append(text)
    run._r.append(fld_end)
    set_run_font(run, FONT_BODY, 8.5, color=GRAY)


def set_page(section, landscape: bool = False) -> None:
    if landscape:
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = Cm(29.7)
        section.page_height = Cm(21.0)
        section.left_margin = Cm(1.5)
        section.right_margin = Cm(1.5)
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.3)
        section.header_distance = Cm(0.8)
        section.footer_distance = Cm(0.7)
    else:
        section.orientation = WD_ORIENT.PORTRAIT
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(2.6)
        section.right_margin = Cm(2.6)
        section.top_margin = Cm(2.4)
        section.bottom_margin = Cm(2.2)
        section.header_distance = Cm(1.3)
        section.footer_distance = Cm(1.2)


def body_width(section) -> float:
    return (section.page_width - section.left_margin - section.right_margin) / 360000.0


def setup_header_footer(section, landscape: bool = False) -> None:
    width = body_width(section)
    section.header.is_linked_to_previous = False
    header = section.header
    p = header.paragraphs[0]
    p.clear()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(width), WD_TAB_ALIGNMENT.RIGHT)
    r = p.add_run("四川大学《数据库系统原理》课程设计")
    set_run_font(r, FONT_BODY, 8.5, color=GRAY)
    r = p.add_run("\t电商订单管理系统")
    set_run_font(r, FONT_BODY, 8.5, color=GRAY)
    p_pr = p._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), BORDER_HEX)
    p_bdr.append(bottom)
    p_pr.append(p_bdr)

    section.footer.is_linked_to_previous = False
    footer = section.footer
    fp = footer.paragraphs[0]
    fp.clear()
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fp.paragraph_format.space_before = Pt(0)
    fp.paragraph_format.space_after = Pt(0)
    r = fp.add_run("第 ")
    set_run_font(r, FONT_BODY, 8.5, color=GRAY)
    add_field(fp, "PAGE")
    r = fp.add_run(" 页")
    set_run_font(r, FONT_BODY, 8.5, color=GRAY)


def start_page_numbering(section, start: int = 1) -> None:
    sect_pr = section._sectPr
    pg_num = sect_pr.find(qn("w:pgNumType"))
    if pg_num is None:
        pg_num = OxmlElement("w:pgNumType")
        sect_pr.append(pg_num)
    pg_num.set(qn("w:start"), str(start))


def continue_page_numbering(section) -> None:
    """移除新分节继承的起始页码，让页码连续。"""
    sect_pr = section._sectPr
    pg_num = sect_pr.find(qn("w:pgNumType"))
    if pg_num is not None and qn("w:start") in pg_num.attrib:
        del pg_num.attrib[qn("w:start")]


def add_heading(doc, text: str, level: int = 1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    if level == 1:
        p_pr = p._p.get_or_add_pPr()
        p_bdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "8")
        bottom.set(qn("w:space"), "5")
        bottom.set(qn("w:color"), NAVY_HEX)
        p_bdr.append(bottom)
        p_pr.append(p_bdr)
    return p


def add_body(doc, text: str, indent: bool = True, size: float = 10.5,
             after: float = 5, color: RGBColor | None = DARK, bold: bool = False,
             line: float = 1.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             keep_with_next: bool = False):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.line_spacing = line
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.keep_with_next = keep_with_next
    if indent:
        p.paragraph_format.first_line_indent = Pt(size * 2)
    run = p.add_run(text)
    set_run_font(run, FONT_BODY, size, bold=bold, color=color)
    return p


def add_bullet(doc, text: str, size: float = 10.5, after: float = 2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Cm(0.74)
    p.paragraph_format.first_line_indent = Cm(-0.37)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(after)
    run = p.add_run("• " + text)
    set_run_font(run, FONT_BODY, size, color=DARK)
    return p


def add_note(doc, text: str, size: float = 9, after: float = 4):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(after)
    run = p.add_run(text)
    set_run_font(run, FONT_BODY, size, color=GRAY)
    return p


def add_caption(doc, text: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    set_run_font(run, FONT_BODY, 9, color=GRAY)
    return p


def add_table(doc, headers: list[str], rows: list[list[str]], widths: list[float],
              font_size: float = 8.8, header_size: float = 8.8,
              center_cols: set[int] | None = None, row_height: float | None = None,
              caption: str | None = None, bold_cols: set[int] | None = None,
              keep_together: bool = False):
    if caption:
        add_caption(doc, caption)
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.allow_autofit = False
    tbl_pr = table._tbl.tblPr
    tbl_w = OxmlElement("w:tblW")
    tbl_w.set(qn("w:w"), str(int(sum(widths) * 567)))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_pr.append(tbl_w)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)
    set_table_borders(table)

    center_cols = center_cols if center_cols is not None else {0}
    bold_cols = bold_cols if bold_cols is not None else set()

    header_row = table.rows[0]
    set_repeat_table_header(header_row)
    set_row_cant_split(header_row)
    for i, text in enumerate(headers):
        cell = header_row.cells[i]
        set_col_width(cell, widths[i])
        set_cell_margins(cell)
        shade_cell(cell, NAVY_HEX)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.1
        run = p.add_run(text)
        set_run_font(run, FONT_UI, header_size, bold=True, color=WHITE)

    for row_idx, values in enumerate(rows, start=1):
        row = table.add_row()
        set_row_cant_split(row)
        if row_height:
            row.height = Cm(row_height)
        for i, text in enumerate(values):
            cell = row.cells[i]
            set_col_width(cell, widths[i])
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if row_idx % 2 == 0:
                shade_cell(cell, PALE_BLUE_HEX)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i in center_cols else WD_ALIGN_PARAGRAPH.LEFT
            lines = str(text).split("\n")
            for j, line in enumerate(lines):
                run = p.add_run(line)
                set_run_font(run, FONT_BODY, font_size, bold=(i in bold_cols), color=DARK)
                if j < len(lines) - 1:
                    run.add_break()
    if keep_together:
        for row in table.rows[:-1]:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.keep_with_next = True
    # 表后留白
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(0)
    spacer.paragraph_format.line_spacing = Pt(4)
    return table


def add_flow_box(doc, steps: list[str]):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.rows[0].cells[0]
    set_col_width(cell, 15.8)
    set_cell_margins(cell, top=0.14, bottom=0.14, left=0.18, right=0.18)
    shade_cell(cell, LIGHT_BLUE_HEX)
    set_cell_border(
        cell,
        left={"val": "single", "sz": 18, "color": NAVY_HEX, "space": 0},
        top={"val": "nil"}, bottom={"val": "nil"}, right={"val": "nil"},
    )
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.35
    run = p.add_run("  →  ".join(steps))
    set_run_font(run, FONT_HEAD, 9.5, bold=True, color=NAVY)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(0)
    spacer.paragraph_format.line_spacing = Pt(4)


def add_code_block(doc, code: str):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.rows[0].cells[0]
    set_col_width(cell, 15.8)
    set_cell_margins(cell, top=0.14, bottom=0.14, left=0.18, right=0.18)
    shade_cell(cell, "F2F2F2")
    set_table_borders(table, color="D9D9D9", size=4)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.1
    lines = code.strip("\n").split("\n")
    for i, line in enumerate(lines):
        run = p.add_run(line)
        set_run_font(run, "Consolas", 8.4, color=RGBColor(0x33, 0x33, 0x33))
        if i < len(lines) - 1:
            run.add_break()
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Pt(0)
    spacer.paragraph_format.space_after = Pt(0)
    spacer.paragraph_format.line_spacing = Pt(4)


def add_picture_fit(doc, path: Path, max_w_cm: float, max_h_cm: float,
                    caption: str | None = None) -> tuple[float, float]:
    with Image.open(path) as im:
        w, h = im.size
    width = max_w_cm
    height = width * h / w
    if height > max_h_cm:
        height = max_h_cm
        width = height * w / h
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run()
    run.add_picture(str(path), width=Cm(width), height=Cm(height))
    if caption:
        add_caption(doc, caption)
    return width, height


# ---------------------------------------------------------------------------
# 文档主体
# ---------------------------------------------------------------------------
def configure_styles(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = FONT_BODY
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = DARK
    normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT_BODY)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(0)

    specs = {
        1: (FONT_HEAD, 16, True, NAVY, 16, 8),
        2: (FONT_HEAD, 13, True, BLUE, 12, 6),
        3: (FONT_HEAD, 11, True, RGBColor(0x33, 0x33, 0x33), 8, 4),
    }
    for level, (name, size, bold, color, before, after) in specs.items():
        style = doc.styles[f"Heading {level}"]
        style.font.name = name
        style.font.size = Pt(size)
        style.font.bold = bold
        style.font.color.rgb = color
        style.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), name)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.line_spacing = 1.2
        style.paragraph_format.keep_with_next = True


def build_cover(doc: Document) -> None:
    add_top_bar(doc, 15.8)
    for _ in range(1):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(PROJECT["university"])
    set_run_font(r, FONT_HEAD, 26, bold=True, color=NAVY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(PROJECT["college"])
    set_run_font(r, FONT_BODY, 13, color=GRAY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(PROJECT["course_full"])
    set_run_font(r, FONT_BODY, 11.5, color=GRAY)

    for _ in range(3):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run("项 目 立 项 材 料")
    set_run_font(r, FONT_BODY, 11, color=GRAY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(PROJECT["name"])
    set_run_font(r, FONT_HEAD, 30, bold=True, color=NAVY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("—— 项目名称、项目描述及功能清单")
    set_run_font(r, FONT_BODY, 13, color=GRAY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(PROJECT["en_name"])
    set_run_font(r, "Times New Roman", 9.5, color=RGBColor(0x7F, 0x7F, 0x7F))

    for _ in range(2):
        doc.add_paragraph()

    info = [
        ("项目类型", "给定方案一（电商订单管理系统）"),
        ("组　　号", f"第 {PROJECT['group_no']} 组"),
        ("小组成员", "________（学号：________）\n________（学号：________）"),
        ("指导教师", PROJECT["instructor"]),
        ("提交日期", PROJECT["date"]),
    ]
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for label, value in info:
        row = table.add_row()
        row.height = Cm(0.9 if label != "小组成员" else 1.3)
        for i, text in enumerate((label, value)):
            cell = row.cells[i]
            set_col_width(cell, 2.8 if i == 0 else 7.8)
            set_cell_margins(cell, top=0.08, bottom=0.08, left=0.12, right=0.12)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_border(cell, bottom={"val": "single", "sz": 4, "color": BORDER_HEX, "space": 0})
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            lines = text.split("\n")
            for j, line in enumerate(lines):
                run = p.add_run(line)
                set_run_font(
                    run,
                    FONT_HEAD if i == 0 else FONT_BODY,
                    9.5 if i == 0 else 10.5,
                    bold=(i == 0),
                    color=NAVY if i == 0 else DARK,
                )
                if j < len(lines) - 1:
                    run.add_break()

    for _ in range(1):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run("SCU · Database Systems Course Project")
    set_run_font(r, "Times New Roman", 8.5, color=RGBColor(0x8C, 0x8C, 0x8C))


def add_top_bar(doc: Document, width_cm: float) -> None:
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    cell = table.rows[0].cells[0]
    set_col_width(cell, width_cm)
    shade_cell(cell, NAVY_HEX)
    set_cell_margins(cell, top=0, bottom=0, left=0, right=0)
    set_table_borders(table, color=NAVY_HEX, size=4)
    table.rows[0].height = Cm(0.22)
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = Pt(1)
    run = p.add_run("")
    set_run_font(run, FONT_BODY, 1)


def build_project_name(doc: Document) -> None:
    add_heading(doc, "一、项目名称", 1)
    rows = [
        ["中文名称", PROJECT["name"]],
        ["英文名称", PROJECT["en_name"]],
        ["项目代号", PROJECT["code"]],
        ["选题类型", f"{PROJECT['scheme']}（电商订单管理系统）"],
        ["一句话定位", "面向中小电商场景，围绕“商品—购物车—订单—支付—库存”主链路构建的 B/S 订单管理系统。"],
    ]
    add_table(
        doc,
        ["项目项", "内容"],
        rows,
        widths=[3.2, 12.6],
        font_size=10,
        header_size=9.5,
        center_cols={0},
        bold_cols={0},
        caption=None,
    )
    add_body(
        doc,
        "本项目选择课程给定方案一。系统保留电商交易与履约的核心链路，不追求营销功能的“大而全”，"
        "重点把订单、库存、支付和统计之间的数据一致性做扎实，使数据库设计、事务控制、约束与多表查询成为项目的核心得分点。",
    )


def build_description(doc: Document) -> None:
    add_heading(doc, "二、项目描述", 1)

    add_heading(doc, "2.1 项目背景", 2)
    for text in DOC_SECTIONS["background"]:
        add_body(doc, text)

    add_heading(doc, "2.2 系统目标与定位", 2)
    for text in DOC_SECTIONS["goals"]:
        add_bullet(doc, text, size=10.5, after=3)
    add_body(doc, "系统的核心业务主线如下：", after=3)
    add_flow_box(doc, FLOW_STEPS)

    add_heading(doc, "2.3 用户角色与权限", 2)
    add_body(
        doc,
        "系统设置游客、普通用户和管理员三类角色。角色差异不仅体现在菜单可见性上，也体现在接口鉴权与数据边界上："
        "普通用户只能访问本人购物车、订单和地址，管理员才能进入商品、库存、用户和统计后台。",
    )
    add_table(
        doc,
        ["角色", "数据范围", "主要权限"],
        [[r["role"], r["scope"], r["permissions"]] for r in ROLES],
        widths=[2.4, 3.2, 10.2],
        font_size=9,
        header_size=9,
        center_cols={0},
        bold_cols={0},
        caption="表 2-1  用户角色与权限划分",
    )

    add_heading(doc, "2.4 核心业务流程", 2)
    add_body(
        doc,
        "一次完整的交易从商品浏览开始：用户按名称、分类或价格区间检索商品，将商品加入购物车并选择数量；"
        "提交订单时选择收货地址，系统在同一个数据库事务中校验库存、写入订单与明细、扣减库存并记录库存流水；"
        "随后用户完成模拟支付，管理员发货，用户确认收货，订单进入完成状态。",
    )
    add_body(
        doc,
        "围绕这条主链路，系统设置三个关键事务点：其一是下单扣库存，必须在同一事务内完成订单、明细、库存和流水的写入；"
        "其二是支付幂等，同一订单重复支付不能产生重复扣款或重复支付记录；其三是取消回补，未支付订单取消后必须把库存加回并留下流水。"
        "三个事务点也是后续异常测试和答辩演示的重点。",
    )

    add_heading(doc, "2.5 项目范围与边界", 2)
    add_body(
        doc,
        "为保证项目在课程周期内可完成、可演示、可讲清，系统对功能范围做了明确取舍。"
        "下表左侧是纳入本次课程设计的范围，右侧是明确不实现的扩展功能。",
    )
    scope_rows = []
    max_len = max(len(SCOPE_IN), len(SCOPE_OUT))
    for i in range(max_len):
        scope_rows.append([
            SCOPE_IN[i] if i < len(SCOPE_IN) else "",
            SCOPE_OUT[i] if i < len(SCOPE_OUT) else "",
        ])
    add_table(
        doc,
        ["纳入范围", "暂不实现"],
        scope_rows,
        widths=[7.9, 7.9],
        font_size=8.8,
        header_size=9,
        center_cols=set(),
        bold_cols=set(),
        caption="表 2-2  项目范围与边界",
    )

    add_heading(doc, "2.6 技术路线与开发环境", 2)
    add_table(
        doc,
        ["层次", "技术选型", "说明"],
        [[t["layer"], t["stack"], t["note"]] for t in TECH_STACK],
        widths=[2.4, 5.8, 7.6],
        font_size=8.8,
        header_size=9,
        center_cols={0},
        bold_cols={0},
        caption="表 2-3  技术路线与开发环境",
    )
    add_note(
        doc,
        "注：技术栈为立项阶段的建议方案，组内确认后可在详细设计中调整；数据库课程的核心仍是关系模型、SQL、事务、约束与索引。",
    )

    add_heading(doc, "2.7 关键业务规则与异常处理", 2)
    add_body(
        doc,
        "课程评分中“异常处理”占 10%，“数据库设计”占 50%。因此本项目把业务规则下沉到数据库约束与服务层事务中，"
        "并对库存不足、重复支付、非法状态流转、重复提交、越权访问等情况给出明确提示。关键规则如下：",
    )
    add_table(
        doc,
        ["规则", "实现方式与异常提示"],
        [[r["rule"], r["implementation"]] for r in BUSINESS_RULES],
        widths=[3.4, 12.4],
        font_size=8.2,
        header_size=8.6,
        center_cols={0},
        bold_cols={0},
        caption="表 2-4  关键业务规则与异常处理",
    )


def build_function_list(doc: Document) -> None:
    add_heading(doc, "三、功能清单", 1)
    add_heading(doc, "3.1 功能结构概览", 2)
    add_body(
        doc,
        "系统共规划 9 个相互关联的核心功能，覆盖账号与权限、商品与分类、购物车、订单、支付、库存、统计和用户地址管理。"
        "前台面向游客与普通用户，后台面向管理员；订单、支付和统计功能同时服务两类角色，但数据边界不同。",
    )
    add_table(
        doc,
        ["编号", "功能名称", "使用角色", "功能概述"],
        [[f["id"], f["name"], f["role"], f["summary"]] for f in FUNCTIONS],
        widths=[1.6, 3.6, 3.2, 7.4],
        font_size=8.6,
        header_size=8.8,
        center_cols={0},
        bold_cols={1},
        caption="表 3-1  系统功能结构概览",
    )
    add_note(
        doc,
        "说明：上表为功能结构索引；完整的功能描述、约束条件、输入/处理/输出和主要数据表见 3.2 节的 Excel 功能清单。",
    )

    add_heading(doc, "3.2 功能清单（Excel 导出）", 2)
    add_body(
        doc,
        "按照课程“功能名称 + 功能描述”的要求，功能清单先在 Excel 中按统一字段整理，再将表格以图片形式嵌入本文件。"
        "Excel 中同时保留“功能清单”“打印1”“打印2”三个工作表：前者用于编辑和筛选，后两者用于导出高清图片。",
    )
    add_note(
        doc,
        "字段口径：功能编号、功能名称、使用角色、功能描述、约束条件与异常处理、输入/处理/输出、主要数据表。"
        "完整可编辑版本见项目仓库 deliverables/软件功能清单.xlsx。",
    )

    # 横向页面：功能清单截图
    sec_landscape = doc.add_section(WD_SECTION.NEW_PAGE)
    set_page(sec_landscape, landscape=True)
    sec_landscape.different_first_page_header_footer = False
    continue_page_numbering(sec_landscape)
    setup_header_footer(sec_landscape, landscape=True)

    add_picture_fit(
        doc,
        ASSETS / "功能清单-1.png",
        max_w_cm=25.8,
        max_h_cm=14.6,
        caption="图 3-1  电商订单管理系统功能清单（1/2）",
    )
    add_note(
        doc,
        "注：图中表格由《软件功能清单.xlsx》的“打印1”工作表导出，可直接在 Excel 中修改后重新生成。",
    )

    doc.add_page_break()
    add_picture_fit(
        doc,
        ASSETS / "功能清单-2.png",
        max_w_cm=25.8,
        max_h_cm=15.6,
        caption="图 3-2  电商订单管理系统功能清单（2/2）",
    )

    # 回到纵向：课程要求对应
    sec_portrait = doc.add_section(WD_SECTION.NEW_PAGE)
    set_page(sec_portrait, landscape=False)
    sec_portrait.different_first_page_header_footer = False
    continue_page_numbering(sec_portrait)
    setup_header_footer(sec_portrait, landscape=False)

    add_heading(doc, "3.3 功能与课程要求对应", 2)
    add_body(
        doc,
        "下表把课程对角色、功能数量、数据表数量、增删改查、多表查询、业务约束和统计查询的要求逐项落到本项目的设计中，"
        "便于检查功能清单是否覆盖评分点。",
    )
    add_table(
        doc,
        ["课程要求", "本项目的落实"],
        [[c["requirement"], c["implementation"]] for c in COURSE_MAPPING],
        widths=[4.6, 11.2],
        font_size=8.8,
        header_size=9,
        center_cols=set(),
        bold_cols=set(),
        caption="表 3-2  功能清单与课程要求对应关系",
    )


def build_database_plan(doc: Document) -> None:
    add_heading(doc, "四、核心数据表规划", 1)
    add_body(
        doc,
        "系统规划 11 张核心表，覆盖用户、地址、分类、商品、库存、库存流水、购物车、购物车明细、订单、订单明细和支付记录。"
        "所有表使用 InnoDB 引擎与 utf8mb4 字符集；金额统一使用 DECIMAL(10,2)，时间统一使用 DATETIME，主键使用 BIGINT UNSIGNED AUTO_INCREMENT。",
    )
    add_table(
        doc,
        ["序号", "表名", "中文名", "关键字段", "作用"],
        [[t["no"], t["name"], t["cn"], t["fields"], t["purpose"]] for t in TABLES],
        widths=[1.0, 3.2, 2.8, 6.4, 2.4],
        font_size=8.0,
        header_size=8.6,
        center_cols={0, 1, 2},
        bold_cols={1},
        caption="表 4-1  核心数据表规划",
    )
    add_body(
        doc,
        "约束设计上，用户表的 username、phone 建唯一索引；购物车表 user_id 唯一，购物车明细对 (cart_id, product_id) 建唯一索引；"
        "库存表 product_id 唯一并设置 stock >= 0 的 CHECK 约束；订单表 order_no、idempotency_key 唯一；支付表 order_id 唯一，"
        "从数据库层兜底支付幂等；订单明细保存 product_name、unit_price、quantity、subtotal 快照，保证历史订单不受商品调价影响。",
    )
    add_heading(doc, "4.1 关键索引与查询效率", 2)
    add_body(
        doc,
        "除主键与外键索引外，针对高频查询规划以下组合索引：",
    )
    for text in [
        "orders(user_id, created_at)：支撑用户订单列表按时间倒序分页。",
        "orders(status, created_at)：支撑后台按订单状态筛选与履约看板。",
        "product(category_id, status)：支撑分类页与上架商品检索。",
        "order_item(order_id)：支撑订单详情与销量聚合。",
        "inventory(stock)：支撑低库存扫描与预警列表。",
    ]:
        add_bullet(doc, text, size=10, after=1)
    add_note(
        doc,
        "注：完整 ER 图、关系模式、字段类型、外键规则与建表脚本将在下一阶段（第 11 周）完成，并作为课程报告 3.2 节的核心内容。",
    )


def build_sql_plan(doc: Document) -> None:
    doc.add_page_break()
    add_heading(doc, "五、SQL 任务规划", 1)
    add_body(
        doc,
        "课程给出 4 项 SQL 任务示例，本项目全部覆盖，并补充低库存和分类销售占比 2 项统计任务。"
        "这些查询将用于接口实现、测试用例和课程报告中的 SQL 说明。",
    )
    add_table(
        doc,
        ["编号", "任务", "涉及表", "主要 SQL 技术"],
        [[s["id"], s["task"], s["tables"], s["techniques"]] for s in SQL_TASKS],
        widths=[1.4, 6.2, 4.4, 3.8],
        font_size=8.5,
        header_size=8.8,
        center_cols={0},
        bold_cols={1},
        keep_together=True,
        caption="表 5-1  SQL 任务规划",
    )

    add_heading(doc, "5.1 示例 SQL：销量最高的前 10 种商品", 2)
    add_body(
        doc,
        "下面的查询演示多表 JOIN、聚合、状态过滤与排序，是课程要求的第 3 项 SQL 任务。"
        "销售额只统计已支付、已发货和已完成订单，避免把取消或未支付订单计入销量。",
    )
    add_code_block(
        doc,
        """
SELECT p.product_id,
       p.name,
       SUM(oi.quantity) AS sales_qty,
       SUM(oi.subtotal) AS sales_amount
FROM order_item oi
JOIN orders o   ON o.order_id = oi.order_id
JOIN product p  ON p.product_id = oi.product_id
WHERE o.status IN ('PAID', 'SHIPPED', 'COMPLETED')
GROUP BY p.product_id, p.name
ORDER BY sales_qty DESC
LIMIT 10;
""",
    )
    add_heading(doc, "5.2 统计口径说明", 2)
    for text in [
        "销售额：按 payment.paid_at 所属月份统计成功支付金额；未支付、已取消订单不计入。",
        "订单量：按 orders.created_at 统计下单数；取消订单单独展示，不与有效订单混算。",
        "销量：按 order_item.quantity 汇总，仅统计 PAID、SHIPPED、COMPLETED 状态的订单。",
    ]:
        add_bullet(doc, text, size=10, after=1)


def build_plan(doc: Document) -> None:
    doc.add_page_break()
    add_heading(doc, "六、后续实施计划", 1)
    add_body(
        doc,
        "本文件完成立项阶段的项目名称、项目描述和功能清单。下一阶段进入数据库详细设计与系统实现，"
        "按“先数据库、再主链路、后统计与界面”的顺序推进，确保每次迭代都有可演示的成果。",
    )
    add_table(
        doc,
        ["阶段", "主要工作", "产出"],
        [[p["phase"], p["work"], p["output"]] for p in PLAN],
        widths=[2.4, 9.2, 4.2],
        font_size=8.8,
        header_size=9,
        center_cols={0},
        bold_cols={0},
        keep_together=True,
        caption="表 6-1  后续实施计划",
    )
    add_body(
        doc,
        "项目仓库将持续记录需求变更、设计决策、接口约定、测试用例和问题清单；"
        "所有交付物由脚本从统一数据源生成，避免 Word、Excel 与代码中的字段口径不一致。",
    )

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.space_before = Pt(18)
    r = p.add_run(f"第 {PROJECT['group_no']} 组")
    set_run_font(r, FONT_BODY, 10.5, color=GRAY)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run(PROJECT["date"])
    set_run_font(r, FONT_BODY, 10.5, color=GRAY)


def build_document(group_no: str = "X", output: Path | None = None) -> Path:
    PROJECT["group_no"] = group_no
    output = output or OUT_DIR / f"第{group_no}组_电商订单管理系统.docx"
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    configure_styles(doc)
    doc.core_properties.title = f"{PROJECT['name']}——项目名称、项目描述及功能清单"
    doc.core_properties.subject = "数据库系统原理课程设计立项材料"
    doc.core_properties.author = f"第 {group_no} 组"
    doc.core_properties.keywords = "电商订单管理系统, 数据库, 课程设计, 功能清单"
    doc.core_properties.comments = "由 scripts/build_deliverables.py 生成"

    # 封面
    sec_cover = doc.sections[0]
    set_page(sec_cover, landscape=False)
    sec_cover.different_first_page_header_footer = True
    build_cover(doc)

    # 正文（纵向，页码从 1 开始）
    sec_body = doc.add_section(WD_SECTION.NEW_PAGE)
    set_page(sec_body, landscape=False)
    sec_body.different_first_page_header_footer = False
    start_page_numbering(sec_body, 1)
    setup_header_footer(sec_body, landscape=False)

    build_project_name(doc)
    build_description(doc)
    build_function_list(doc)
    build_database_plan(doc)
    build_sql_plan(doc)
    build_plan(doc)

    doc.save(output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", default="X")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    print(build_document(args.group, args.out))
