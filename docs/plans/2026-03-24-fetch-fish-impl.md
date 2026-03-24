# Fetch Fish Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI reading tool supporting WeRead and PDF with chapter navigation and paginated scrolling.

**Architecture:** Python CLI with argparse, unified Book interface, pluggable providers for WeRead (API + SQLite cache) and PDF (PyMuPDF).

**Tech Stack:** Python 3.10+, argparse, PyMuPDF, sqlite3

---

## Stage 1: Project Setup

### Task 1: Create requirements.txt and config.py

**Files:**
- Create: `requirements.txt`
- Create: `config.py`

**Step 1: Create requirements.txt**

```
PyMuPDF>=1.23.0
```

**Step 2: Create config.py**

```python
"""Configuration management for fetch-fish."""
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".fetch-fish"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_DIR = CONFIG_DIR / "cache"


def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_dirs()
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(config: dict):
    ensure_dirs()
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
```

**Step 3: Run to verify**

```bash
cd .worktrees/impl && python -c "import config; print(config.CONFIG_DIR)"
```

Expected: `~/.fetch-fish`

**Step 4: Commit**

```bash
git add requirements.txt config.py
git commit -m "feat: add project setup and config"
```

---

## Stage 2: Base Provider Interface

### Task 2: Create Book and Chapter data classes

**Files:**
- Create: `providers/base.py`
- Create: `providers/__init__.py`

**Step 1: Create providers/base.py**

```python
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
```

**Step 2: Create providers/__init__.py**

```python
"""Book providers."""
from providers.base import Book, Chapter

__all__ = ["Book", "Chapter"]
```

**Step 3: Verify**

```bash
cd .worktrees/impl && python -c "from providers.base import Book, Chapter; print('OK')"
```

**Step 4: Commit**

```bash
git add providers/base.py providers/__init__.py
git commit -m "feat: add base Book/Chapter interfaces"
```

---

## Stage 3: PDF Provider

### Task 3: Create PDF provider

**Files:**
- Create: `providers/pdf.py`

**Step 1: Write test**

```python
# tests/test_pdf.py
import pytest
import sys
sys.path.insert(0, ".")
from providers.pdf import PDFBook


def test_pdf_open_missing_file():
    with pytest.raises(FileNotFoundError):
        PDFBook("/nonexistent/file.pdf")
```

**Step 2: Run test to verify it fails**

```bash
cd .worktrees/impl && python -m pytest tests/test_pdf.py -v
```

Expected: FAIL - module not found

**Step 3: Create PDF provider**

```python
"""PDF book provider using PyMuPDF."""
import fitz  # PyMuPDF
from dataclasses import dataclass
from typing import List
from providers.base import Book, Chapter


@dataclass
class PDFBook(Book):
    """PDF book implementation."""
    path: str
    title: str = ""
    author: str = "Unknown"
    source: str = "pdf"

    def __post_init__(self):
        self._doc = fitz.open(self.path)
        if not self.title:
            self.title = self._doc.metadata.get("title") or self._doc.name

    def get_chapters(self) -> List[Chapter]:
        toc = self._doc.get_toc()
        chapters = []
        for i, (level, title, page) in enumerate(toc):
            if level == 1:
                chapters.append(Chapter(
                    index=len(chapters),
                    title=title or f"Page {page}",
                    chapter_id=str(page)
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
```

**Step 4: Run test**

```bash
cd .worktrees/impl && python -m pytest tests/test_pdf.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add providers/pdf.py tests/test_pdf.py
git commit -m "feat: add PDF provider with PyMuPDF"
```

---

## Stage 4: WeRead Provider (Basic)

### Task 4: Create WeRead provider stub with cookie auth

**Files:**
- Create: `providers/weread.py`
- Create: `storage/cache.py`

**Step 1: Create storage/cache.py**

```python
"""SQLite cache for WeRead books."""
import sqlite3
from pathlib import Path
from typing import Optional
import config

DB_FILE = config.CACHE_DIR / "weread.db"


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            title TEXT,
            author TEXT,
            cover_url TEXT,
            updated_at INTEGER
        );
        CREATE TABLE IF NOT EXISTS chapters (
            id TEXT PRIMARY KEY,
            book_id TEXT,
            idx INTEGER,
            title TEXT,
            start_offset INTEGER
        );
        CREATE TABLE IF NOT EXISTS content (
            chapter_id TEXT,
            offset INTEGER,
            text TEXT,
            PRIMARY KEY (chapter_id, offset)
        );
    """)
    db.commit()
    return db
```

**Step 2: Create providers/weread.py (stub)**

```python
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
```

**Step 3: Verify**

```bash
cd .worktrees/impl && python -c "from providers.weread import WeReadBook; print('OK')"
```

**Step 4: Commit**

```bash
git add providers/weread.py storage/cache.py
git commit -m "feat: add WeRead provider stub with SQLite cache"
```

---

## Stage 5: CLI Reader

### Task 5: Create interactive reader

**Files:**
- Create: `reader.py`

**Step 1: Write minimal reader**

```python
"""Interactive CLI reader."""
import sys
from typing import Callable


def read_book(
    get_page: Callable[[int, int], tuple[str, int]],
    title: str,
    author: str = ""
):
    """Interactive reading loop."""
    page = 0
    page_size = 500

    while True:
        content, total = get_page(page, page_size)
        if not content:
            print("\n[End of book]")
            break

        # Simple display with pagination
        lines = content.split("\n")
        for line in lines[:30]:  # 30 lines per screen
            print(line)

        print(f"\n[page {page + 1}/{total}] Enter=next, q=quit")

        cmd = input().strip().lower()
        if cmd == "q":
            break
        elif cmd == "":
            page += 1
        else:
            page = int(cmd) - 1 if cmd.isdigit() else page
```

**Step 2: Commit**

```bash
git add reader.py
git commit -m "feat: add basic interactive reader"
```

---

## Stage 6: Main CLI

### Task 6: Create CLI entry point

**Files:**
- Create: `cli.py`

**Step 1: Create CLI**

```python
"""fetch-fish CLI entry point."""
import argparse
import sys
import config
from providers.pdf import PDFBook
from providers.weread import WeReadBook
from reader import read_book


def cmd_weread_list(args):
    """List WeRead books from cache."""
    from storage.cache import get_db
    db = get_db()
    books = db.execute("SELECT id, title, author FROM books").fetchall()
    if not books:
        print("No books cached. Set weread_cookie in config first.")
        return
    for b in books:
        print(f"{b['id']}  {b['title']} - {b['author']}")


def cmd_weread_read(args):
    """Read a WeRead book."""
    book = WeReadBook(book_id=args.book_id)
    read_book(book.get_page, book.title, book.author)


def cmd_pdf_open(args):
    """Open and read a PDF."""
    try:
        book = PDFBook(path=args.path)
    except FileNotFoundError:
        print(f"File not found: {args.path}")
        return
    read_book(book.get_page, book.title, book.author)


def cmd_set_cookie(args):
    """Set WeRead cookie."""
    cfg = config.load_config()
    cfg["weread_cookie"] = args.cookie
    config.save_config(cfg)
    print("Cookie saved.")


def main():
    parser = argparse.ArgumentParser(description="fetch-fish: CLI book reader")
    sub = parser.add_subparsers()

    # WeRead commands
    p_weread = sub.add_parser("weread", help="WeRead commands")
    p_weread.add_parser("list", help="List cached books").set_defaults(func=cmd_weread_list)
    p_weread.add_parser("read", help="Read a book").add_argument("book_id").set_defaults(func=cmd_weread_read)

    # PDF command
    p_pdf = sub.add_parser("pdf", help="PDF commands")
    p_pdf.add_parser("open", help="Open PDF").add_argument("path").set_defaults(func=cmd_pdf_open)

    # Config command
    p_config = sub.add_parser("config", help="Configuration")
    p_config.add_parser("set-cookie", help="Set WeRead cookie").add_argument("cookie").set_defaults(func=cmd_set_cookie)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

**Step 2: Run basic test**

```bash
cd .worktrees/impl && python cli.py --help
```

Expected: Show help message

**Step 3: Commit**

```bash
git add cli.py
git commit -m "feat: add CLI entry point with weread and pdf commands"
```

---

## Stage 7: WeRead API Integration

### Task 7: Implement WeRead API (stub with proper headers)

**Files:**
- Modify: `providers/weread.py`

**Step 1: Add API methods to weread.py**

```python
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
```

**Step 2: Commit**

```bash
git add providers/weread.py
git commit -m "feat: add WeRead API fetch methods"
```

---

## Stage 8: Project Finalization

### Task 8: Finalize project structure

**Files:**
- Verify all files present

**Step 1: Verify structure**

```bash
cd .worktrees/impl && find . -type f -name "*.py" | sort
```

Expected:
```
./cli.py
./config.py
./providers/base.py
./providers/pdf.py
./providers/weread.py
./reader.py
./storage/cache.py
```

**Step 2: Final commit**

```bash
git add -A && git commit -m "feat: complete fetch-fish implementation"
```

---

## Summary

| Task | Description |
|------|-------------|
| 1 | Project setup (requirements.txt, config.py) |
| 2 | Base Book/Chapter interfaces |
| 3 | PDF provider (PyMuPDF) |
| 4 | WeRead provider stub + SQLite cache |
| 5 | Interactive reader |
| 6 | CLI entry point |
| 7 | WeRead API integration |
| 8 | Finalize and commit |
