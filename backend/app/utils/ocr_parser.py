"""OCR 解析器 — 对应 Task 9.2, 9.4
支持扫描件 PDF 页面图片和独立图片文件的 OCR 识别"""

from __future__ import annotations

from typing import Optional


class OCRParser:
    """OCR 解析器：基于 PaddleOCR 进行文字识别"""

    _ocr = None

    @classmethod
    def _get_ocr(cls):
        """延迟加载 PaddleOCR 实例"""
        if cls._ocr is None:
            try:
                from paddleocr import PaddleOCR
                cls._ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang="ch",
                    use_gpu=False,
                    show_log=False,
                )
            except ImportError:
                raise RuntimeError(
                    "OCR 解析需要安装 PaddleOCR: pip install paddlepaddle paddleocr"
                )
        return cls._ocr

    @classmethod
    def recognize_image(cls, image_bytes: bytes) -> str:
        """识别单张图片中的文字"""
        ocr = cls._get_ocr()
        import numpy as np
        from PIL import Image

        image = Image.open(__import__("io").BytesIO(image_bytes))
        img_array = np.array(image)
        result = ocr.ocr(img_array, cls=False)

        if not result or not result[0]:
            return ""

        lines = []
        for line_info in result[0]:
            text = line_info[1][0]
            if text:
                lines.append(text)
        return "\n".join(lines)

    @classmethod
    def is_available(cls) -> bool:
        """检查 OCR 是否可用"""
        try:
            cls._get_ocr()
            return True
        except RuntimeError:
            return False
