# -*- coding: utf-8 -*-
"""一键生成 M1 立项材料：Excel → 功能清单图 → Word → Markdown 文档 → 预览。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_docs import build_docs
from build_excel import build_workbook
from build_word import build_document
from export_images import export_images


def main() -> int:
    parser = argparse.ArgumentParser(description="生成电商订单管理系统立项材料")
    parser.add_argument("--group", default="X", help="组号，默认 X（占位）")
    parser.add_argument("--no-preview", action="store_true", help="跳过 Word PDF 预览")
    parser.add_argument("--skip-images", action="store_true", help="跳过 Excel 截图导出，复用 assets 中已有图片")
    args = parser.parse_args()

    group = str(args.group).strip() or "X"

    print(f"[1/5] 生成 Excel：软件功能清单.xlsx（第 {group} 组）")
    xlsx = build_workbook(group)

    if args.skip_images:
        print("[2/5] 跳过图片导出，复用 assets/功能清单-1.png、功能清单-2.png")
        for name in ("功能清单-1.png", "功能清单-2.png"):
            if not (ROOT / "assets" / name).exists():
                print(f"  ! 缺少 {name}，请先运行不带 --skip-images 的完整构建")
                return 1
    else:
        print("[2/5] 导出功能清单图片：assets/功能清单-1.png、功能清单-2.png")
        export_images(xlsx)

    print(f"[3/5] 生成 Word：第{group}组_电商订单管理系统.docx")
    docx = build_document(group)

    print("[4/5] 生成 Markdown 文档：docs/01-requirements.md、docs/02-database-design.md")
    build_docs(group)

    if not args.no_preview:
        print("[5/5] 生成 Word PDF 预览（需要本机安装 Microsoft Word）")
        try:
            from export_word_preview import export_preview

            export_preview(docx)
        except Exception as exc:  # 预览失败不影响交付物
            print(f"  ! 预览生成失败（不影响 docx/xlsx）：{exc}")
    else:
        print("[5/5] 已跳过错预览")

    print("\n完成。交付物：")
    print(f"  - {xlsx.relative_to(ROOT)}")
    print(f"  - {docx.relative_to(ROOT)}")
    print(f"  - {ROOT / 'assets' / '功能清单-1.png'}")
    print(f"  - {ROOT / 'assets' / '功能清单-2.png'}")
    print("\n提示：如组号尚未确定，可先使用第X组占位；确定后运行：")
    print("  python scripts/build_deliverables.py --group 7")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
