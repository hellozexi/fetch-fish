"""WeRead book provider."""
import json
import requests
from typing import List, Optional
from providers.base import Book, Chapter
import config
from storage.cache import init_db, get_db


class WeReadBook(Book):
    """WeRead book implementation."""
    source = "weread"

    def __init__(self, book_id: str, title: str = "", author: str = ""):
        self.book_id = book_id
        self.title = title
        self.author = author
        self._chapters: Optional[List[Chapter]] = None

    @property
    def cookie(self) -> Optional[str]:
        cfg = config.load_config()
        return cfg.get("weread_cookie")

    def get_chapters(self) -> List[Chapter]:
        if self._chapters is not None:
            return self._chapters
        db = get_db()
        rows = db.execute(
            "SELECT id, title FROM chapters WHERE book_id=? ORDER BY idx",
            (self.book_id,)
        ).fetchall()
        self._chapters = [
            Chapter(index=i, title=row["title"], chapter_id=row["id"])
            for i, row in enumerate(rows)
        ]
        return self._chapters

    def get_content(self, chapter_id: str) -> str:
        db = get_db()
        rows = db.execute(
            "SELECT text FROM content WHERE chapter_id=? ORDER BY offset",
            (chapter_id,)
        ).fetchall()
        return "\n".join(r["text"] for r in rows)

    def get_page(self, page_num: int, page_size: int = 500) -> tuple[str, int]:
        chapters = self.get_chapters()
        if not chapters:
            return "", 0
        idx = min(page_num, len(chapters) - 1)
        content = self.get_content(chapters[idx].chapter_id)
        return content[:page_size], len(chapters)

    def fetch_booklist(self) -> List[dict]:
        """Fetch booklist from WeRead API."""
        if not self.cookie:
            raise ValueError("WeRead cookie not set. Run: fetch-fish config set-cookie <cookie>")
        url = "https://weread.qq.com/web/bookList"
        headers = {"Cookie": self.cookie}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json().get("books", [])

    def cache_books(self):
        """Cache booklist to database."""
        books = self.fetch_booklist()
        db = get_db()
        for b in books:
            db.execute(
                "INSERT OR REPLACE INTO books (id, title, author) VALUES (?, ?, ?)",
                (b["bookId"], b["title"], b["author"])
            )
        db.commit()