"""PDF book provider using PyMuPDF."""
import fitz  # PyMuPDF
from typing import List
from providers.base import Book, Chapter


class PDFBook(Book):
    """PDF book implementation."""

    def __init__(self, path: str, title: str = "", author: str = "Unknown", source: str = "pdf"):
        self.path = path
        self.book_id = path
        self.title = title
        self.author = author
        self.source = source
        try:
            self._doc = fitz.open(path)
        except fitz.FileNotFoundError as e:
            raise FileNotFoundError(str(e)) from e
        if not self.title:
            self.title = self._doc.metadata.get("title") or self._doc.name

    def get_chapters(self) -> List[Chapter]:
        toc = self._doc.get_toc()
        chapters = []
        for i, (level, title, page) in enumerate(toc):
            if level == 1:
                # PDF TOC pages are 1-based, PyMuPDF is 0-based
                chapters.append(Chapter(
                    index=len(chapters),
                    title=title or f"Page {page}",
                    chapter_id=str(page - 1)
                ))
        if not chapters:
            chapters.append(Chapter(index=0, title="Start", chapter_id="0"))
        return chapters

    def get_content(self, chapter_id: str) -> str:
        page_num = int(chapter_id)
        page = self._doc[page_num]
        return page.get_text()

    def get_page(self, page_num: int, page_size: int = 500) -> tuple[str, int]:
        total = len(self._doc)
        if page_num < 0:
            page_num = 0
        elif page_num >= total:
            page_num = total - 1
        page = self._doc[page_num]
        return page.get_text(), total

    def __del__(self):
        if hasattr(self, "_doc"):
            self._doc.close()