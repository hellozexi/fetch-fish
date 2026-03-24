"""Base provider interface for book sources."""
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List, Optional


@dataclass
class Chapter:
    """Represents a book chapter."""
    index: int
    title: str
    chapter_id: str


@dataclass
class Book:
    """Represents a book."""
    book_id: str
    title: str
    author: str
    source: str  # "weread" or "pdf"

    @abstractmethod
    def get_chapters(self) -> List[Chapter]:
        """Get table of contents."""
        pass

    @abstractmethod
    def get_content(self, chapter_id: str) -> str:
        """Get full content of a chapter."""
        pass

    @abstractmethod
    def get_page(self, page_num: int, page_size: int) -> tuple[str, int]:
        """Get page content and total pages.

        Returns (content, total_pages).
        """
        pass