from __future__ import annotations

from typing import List, Optional, Tuple

TEXT_MIN_CHARS = 10


def pdf_to_text_and_images(file_bytes: bytes, dpi: int = 150) -> Tuple[str, List[bytes]]:
    """将 PDF 拆为：可提取文本 + 需视觉解析的页面图片（扫描页）。"""
    import fitz

    text_parts: List[str] = []
    scanned_images: List[bytes] = []

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        for page in doc:
            page_text = page.get_text().strip()
            if len(page_text) >= TEXT_MIN_CHARS:
                text_parts.append(page_text)
            else:
                pix = page.get_pixmap(dpi=dpi)
                scanned_images.append(pix.tobytes("png"))
    finally:
        doc.close()

    return "\n\n".join(text_parts), scanned_images


def docx_to_text(file_bytes: bytes) -> str:
    """提取 Word 文档全文（兼容 .docx / Word2003 XML / HTML 三种 .doc 变体）。"""
    import os
    import tempfile

    from app.utils.docx_parser import DOCXParser

    with tempfile.NamedTemporaryFile(suffix=".doc", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        return DOCXParser.get_full_text(tmp_path)
    finally:
        os.unlink(tmp_path)


def load_document_payload(
    file_bytes: bytes, file_ext: str
) -> Tuple[Optional[str], List[bytes]]:
    """根据扩展名归一化为 (文本, 图片字节列表)，供 Agent 直接消费。"""
    ext = file_ext.lower()

    if ext == ".pdf":
        text, images = pdf_to_text_and_images(file_bytes)
        return (text or None), images
    if ext in (".doc", ".docx"):
        return (docx_to_text(file_bytes) or None), []
    if ext in (".jpg", ".jpeg", ".png"):
        return None, [file_bytes]

    return None, []
