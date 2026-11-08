# -*- coding: utf-8 -*-
"""把 Excel 的“打印1 / 打印2”工作表导出为高清 PNG，供 Word 嵌入。"""

from __future__ import annotations

import argparse
from pathlib import Path

import pymupdf
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
PREVIEW = ASSETS / "preview"


def _crop_white(src: Path, dst: Path, padding: int = 28) -> tuple[int, int]:
    img = Image.open(src).convert("RGB")
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bbox = ImageChops.difference(img, bg).getbbox()
    if bbox:
        left = max(0, bbox[0] - padding)
        top = max(0, bbox[1] - padding)
        right = min(img.width, bbox[2] + padding)
        bottom = min(img.height, bbox[3] + padding)
        img = img.crop((left, top, right, bottom))
    img.save(dst, dpi=(300, 300))
    return img.size


def _pdf_to_png(pdf: Path, png: Path, dpi: int = 300) -> tuple[int, int]:
    doc = pymupdf.open(pdf)
    try:
        if doc.page_count < 1:
            raise RuntimeError(f"PDF 没有页面：{pdf}")
        page = doc[0]
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        tmp = png.with_suffix(".raw.png")
        pix.save(tmp)
    finally:
        doc.close()
    try:
        return _crop_white(tmp, png)
    finally:
        tmp.unlink(missing_ok=True)


def export_images(xlsx: Path | None = None) -> list[Path]:
    import win32com.client

    xlsx = (xlsx or ROOT / "deliverables" / "软件功能清单.xlsx").resolve()
    ASSETS.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)

    jobs = [
        ("打印1", "A1:G8", ASSETS / "功能清单-1.png", PREVIEW / "功能清单-1.pdf"),
        ("打印2", "A1:G9", ASSETS / "功能清单-2.png", PREVIEW / "功能清单-2.pdf"),
    ]

    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    excel.ScreenUpdating = False
    wb = None
    try:
        wb = excel.Workbooks.Open(str(xlsx), ReadOnly=True)
        for sheet_name, area, png, pdf in jobs:
            ws = wb.Worksheets(sheet_name)
            ws.Activate()
            ps = ws.PageSetup
            ps.Orientation = 2  # xlLandscape
            ps.PaperSize = 9  # xlPaperA4
            ps.Zoom = False
            ps.FitToPagesWide = 1
            ps.FitToPagesTall = 1
            ps.PrintArea = area
            ps.LeftMargin = excel.InchesToPoints(0.31)
            ps.RightMargin = excel.InchesToPoints(0.31)
            ps.TopMargin = excel.InchesToPoints(0.30)
            ps.BottomMargin = excel.InchesToPoints(0.30)
            ps.HeaderMargin = excel.InchesToPoints(0.15)
            ps.FooterMargin = excel.InchesToPoints(0.15)
            ps.CenterHorizontally = True
            ps.PrintGridlines = False
            ws.ExportAsFixedFormat(0, str(pdf))  # 0 = xlTypePDF
            _pdf_to_png(pdf, png)
            print(f"已生成 {png.relative_to(ROOT)}  ({png.stat().st_size / 1024:.0f} KB)")
    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        excel.Quit()
        del excel
    return [j[2] for j in jobs]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--xlsx", type=Path, default=None)
    args = parser.parse_args()
    export_images(args.xlsx)
