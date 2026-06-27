"""DOCX 文档解析器 — 对应 Task 9.3"""

from __future__ import annotations

from typing import List


class DOCXChunk:
    """DOCX 文本片段"""
    def __init__(self, chunk_index: int, content: str):
        self.chunk_index = chunk_index
        self.content = content


class DOCXParser:
    """DOCX 解析器：按段落提取文本，每段不超过 1000 字符"""

    MAX_CHUNK_SIZE = 1000

    @staticmethod
    def parse(file_path: str) -> List[DOCXChunk]:
        """解析 DOCX 文件，按段落分片"""
        try:
            import docx
        except ImportError:
            raise RuntimeError("DOCX 解析需要安装 python-docx: pip install python-docx")

        doc = docx.Document(file_path)
        chunks: List[DOCXChunk] = []
        chunk_index = 0
        current_chunk = ""

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                if current_chunk:
                    chunks.append(DOCXChunk(chunk_index, current_chunk))
                    chunk_index += 1
                    current_chunk = ""
                continue

            # 按最大长度分片
            if len(current_chunk) + len(text) + 1 <= DOCXParser.MAX_CHUNK_SIZE:
                current_chunk = (current_chunk + "\n" + text) if current_chunk else text
            else:
                if current_chunk:
                    chunks.append(DOCXChunk(chunk_index, current_chunk))
                    chunk_index += 1
                current_chunk = text

            # 如果当前 chunk 已超过最大长度，按字符拆分
            while len(current_chunk) > DOCXParser.MAX_CHUNK_SIZE:
                split_at = current_chunk.rfind("\n", 0, DOCXParser.MAX_CHUNK_SIZE)
                if split_at < 0:
                    split_at = current_chunk.rfind(" ", 0, DOCXParser.MAX_CHUNK_SIZE)
                if split_at < 0:
                    split_at = DOCXParser.MAX_CHUNK_SIZE
                chunks.append(DOCXChunk(chunk_index, current_chunk[:split_at]))
                chunk_index += 1
                current_chunk = current_chunk[split_at:].strip()

        if current_chunk:
            chunks.append(DOCXChunk(chunk_index, current_chunk))

        return chunks

    @staticmethod
    def get_full_text(file_path: str) -> str:
        """获取 DOCX 完整文本"""
        try:
            import docx
            doc = docx.Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            raise RuntimeError("DOCX 解析需要安装 python-docx: pip install python-docx")
