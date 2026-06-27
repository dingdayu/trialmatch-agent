"""PDF 文档解析器 — 对应 Task 9.1, 9.2"""

from __future__ import annotations

import io
from typing import List, Optional


class PDFPage:
    """PDF 页面内容"""
    def __init__(self, page_no: int, text: str, is_scanned: bool = False):
        self.page_no = page_no
        self.text = text
        self.is_scanned = is_scanned


class PDFParser:
    """PDF 解析器：优先文字版提取，扫描件回退 OCR"""

    @staticmethod
    def parse(file_path: str, force_ocr: bool = False) -> List[PDFPage]:
        """解析 PDF 文件，返回每页内容"""
        pages: List[PDFPage] = []

        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise RuntimeError("PDF 解析需要安装 PyMuPDF: pip install PyMuPDF")

        doc = fitz.open(file_path)
        try:
            for i in range(len(doc)):
                page = doc[i]
                text = page.get_text().strip()

                if text and not force_ocr:
                    pages.append(PDFPage(page_no=i + 1, text=text, is_scanned=False))
                else:
                    # 扫描件：提取页面图片供 OCR 处理
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")
                    pages.append(PDFPage(
                        page_no=i + 1,
                        text="",
                        is_scanned=True,
                    ))
                    # 存储图片数据在额外属性中
                    pages[-1]._image_bytes = img_bytes  # type: ignore
        finally:
            doc.close()

        return pages

    @staticmethod
    def get_page_count(file_path: str) -> int:
        """获取 PDF 页数"""
        try:
            import fitz
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except ImportError:
            return 0
