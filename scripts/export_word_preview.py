# -*- coding: utf-8 -*-
"""用 Word COM 将 docx 导出为 PDF，并渲染为页面 PNG，便于本地检查排版。"""

from __future__ import annotations

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "assets" / "preview"


def export_preview(docx_path: Path, dpi: int = 110) -> tuple[Path, int]:
    import win32com.client

    docx_path = docx_path.resolve()
    PREVIEW.mkdir(parents=True, exist_ok=True)
    pdf_path = PREVIEW / "word-preview.pdf"

    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = None
    try:
        doc = word.Documents.Open(str(docx_path), ReadOnly=True)
        doc.ExportAsFixedFormat(str(pdf_path), 17)  # wdExportFormatPDF
    finally:
        if doc is not None:
            doc.Close(False)
        word.Quit()
        del word

    pdf = pymupdf.open(pdf_path)
    try:
        for i, page in enumerate(pdf):
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            pix.save(PREVIEW / f"page-{i + 1:02d}.png")
        page_count = pdf.page_count
    finally:
        pdf.close()

    print(f"预览已生成：{pdf_path.relative_to(ROOT)}（{page_count} 页）")
    return pdf_path, page_count


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=110)
    args = parser.parse_args()
    export_preview(args.docx, args.dpi)
