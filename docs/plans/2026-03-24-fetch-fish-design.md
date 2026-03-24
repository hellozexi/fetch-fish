# Fetch Fish Design

## Overview

CLI tool for reading WeRead (微信读书) and PDF books in terminal.

## Architecture

```
┌─────────────────────────────────────────────┐
│                   CLI 界面                  │
│         (argparse - 阅读器交互)              │
└─────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
┌───────────────┐           ┌───────────────┐
│  微信读书模块   │           │    PDF 模块    │
│  - Cookie 认证 │           │  - PyMuPDF    │
│  - API 请求    │           │  - 本地文件    │
│  - 本地缓存    │           │  - 实时解析    │
└───────────────┘           └───────────────┘
        │                           │
        ▼                           ▼
┌───────────────┐           ┌───────────────┐
│   SQLite      │           │  文件系统      │
│   (书籍/笔记)  │           │  (PDF 文件)    │
└───────────────┘           └───────────────┘
```

## Data Models

### WeRead Cache (SQLite)

```sql
-- 书籍表
books (id, title, author, cover_url, updated_at)

-- 章节表
chapters (id, book_id, index, title, start_offset)

-- 内容表（按需加载）
content (chapter_id, offset, text)
```

### PDF Structure

```python
class PDFBook:
    path: str
    title: str
    chapters: List[Chapter]  # 从 TOC 提取
    total_pages: int
```

### Unified Interface

```python
class Book:
    def get_chapters() -> List[Chapter]
    def get_content(chapter_id) -> str
    def get_page(page_num, page_size) -> str
```

## CLI Interaction

### Commands

```bash
# WeRead
fetch-fish weread list              # List bookshelf
fetch-fish weread read <book_id>    # Read book

# PDF
fetch-fish pdf open <path>          # Open PDF file

# In-reader commands
: chapters     # Show chapter list
: goto <n>     # Jump to chapter N
: next         # Next page
: prev         # Previous page
: search <kw>  # Search
: quit         # Exit
```

### Reader Interface

```
《书名》 作者
━━━━━━━━━━━━━━━━━━━━
第 3 章 标题
━━━━━━━━━━━━━━━━━━━━
这是正文内容...

[page 3/120] :help 查看命令
```

## Error Handling & Persistence

### Cookie Management

```json
// ~/.fetch-fish/config.json
{
    "weread_cookie": "...",
    "cache_dir": "~/.fetch-fish/cache"
}
```

### Error Handling

- Cookie expired → Prompt to re-import
- Network error → Show cached content if available
- PDF corrupted → Friendly error message
- Chapter fetch failed → Skip or retry

### Offline Support

- WeRead: Cached book data, readable offline
- PDF: Local files, no network required

## Project Structure

```
fetch-fish/
├── cli.py              # Entry point
├── reader.py           # Unified reader
├── providers/
│   ├── __init__.py
│   ├── base.py         # Abstract interface
│   ├── weread.py       # WeRead provider
│   └── pdf.py          # PDF provider
├── storage/
│   ├── __init__.py
│   └── cache.py        # SQLite cache
├── config.py           # Config management
└── requirements.txt
```

## Tech Stack

- Python 3.10+
- argparse (CLI)
- PyMuPDF (PDF parsing)
- sqlite3 (WeRead cache)
