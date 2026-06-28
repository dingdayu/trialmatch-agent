"""DOCX 文档解析器 — 对应 Task 9.3"""

from __future__ import annotations

from typing import List


class DOCXChunk:
    """DOCX 文本片段"""
    def __init__(self, chunk_index: int, content: str):
        self.chunk_index = chunk_index
        self.content = content


class DOCXParser:
    """Word 文档解析器：自动识别 OOXML(.docx)、Word2003 XML、HTML 三种 .doc/.docx 变体"""

    MAX_CHUNK_SIZE = 1000

    @staticmethod
    def parse(file_path: str) -> List[DOCXChunk]:
        """解析 Word 文档，按段落分片"""
        paragraphs = DOCXParser._extract_paragraphs(file_path)
        return DOCXParser._chunk_paragraphs(paragraphs)

    @staticmethod
    def get_full_text(file_path: str) -> str:
        """获取 Word 文档完整文本"""
        return "\n".join(DOCXParser._extract_paragraphs(file_path))

    @staticmethod
    def _extract_paragraphs(file_path: str) -> List[str]:
        with open(file_path, "rb") as f:
            head = f.read(8)

        if head[:2] == b"PK":
            return DOCXParser._extract_ooxml(file_path)

        text_head = head.lstrip().lower()
        if text_head.startswith(b"<?xml") or text_head.startswith(b"<w:") or text_head.startswith(b"<html") or text_head.startswith(b"<!doc"):
            return DOCXParser._extract_xml_or_html(file_path)

        if head[:4] == b"\xd0\xcf\x11\xe0":
            raise RuntimeError("旧版二进制 .doc 暂不支持，请转存为 .docx 或 PDF 后重新上传")

        return DOCXParser._extract_xml_or_html(file_path)

    @staticmethod
    def _extract_ooxml(file_path: str) -> List[str]:
        try:
            import docx
        except ImportError:
            raise RuntimeError("DOCX 解析需要安装 python-docx: pip install python-docx")

        doc = docx.Document(file_path)
        return [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    @staticmethod
    def _extract_xml_or_html(file_path: str) -> List[str]:
        from lxml import etree

        with open(file_path, "rb") as f:
            data = f.read()

        parser = etree.XMLParser(recover=True, huge_tree=True)
        try:
            root = etree.fromstring(data, parser=parser)
        except etree.XMLSyntaxError:
            root = None

        if root is not None:
            wordml_ns = "http://schemas.microsoft.com/office/word/2003/wordml"
            paragraphs: List[str] = []
            for para in root.iter(f"{{{wordml_ns}}}p"):
                text = "".join(
                    node.text or "" for node in para.iter(f"{{{wordml_ns}}}t")
                ).strip()
                if text:
                    paragraphs.append(text)
            if paragraphs:
                return paragraphs

        return DOCXParser._extract_html(data)

    @staticmethod
    def _extract_html(data: bytes) -> List[str]:
        from lxml import html as lxml_html

        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:
            text = data.decode("latin-1", errors="ignore")

        tree = lxml_html.fromstring(text)
        for bad in tree.xpath("//script | //style"):
            bad.getparent().remove(bad)

        lines = [line.strip() for line in tree.itertext()]
        return [line for line in lines if line]

    @staticmethod
    def _chunk_paragraphs(paragraphs: List[str]) -> List[DOCXChunk]:
        chunks: List[DOCXChunk] = []
        chunk_index = 0
        current_chunk = ""

        for text in paragraphs:
            if len(current_chunk) + len(text) + 1 <= DOCXParser.MAX_CHUNK_SIZE:
                current_chunk = (current_chunk + "\n" + text) if current_chunk else text
            else:
                if current_chunk:
                    chunks.append(DOCXChunk(chunk_index, current_chunk))
                    chunk_index += 1
                current_chunk = text

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
