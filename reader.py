"""Interactive CLI reader."""
import json
import os
import sys
import tty
import termios
from pathlib import Path
from typing import Callable, Optional

PROGRESS_DIR = Path.home() / ".fetch-fish" / "progress"
PROGRESS_DIR.mkdir(parents=True, exist_ok=True)


def get_progress_path(book_id: str) -> Path:
    """Get progress file path for a book."""
    import hashlib
    h = hashlib.md5(book_id.encode()).hexdigest()[:12]
    return PROGRESS_DIR / f"{h}.json"


def save_progress(book_id: str, page: int, total: int):
    """Save reading progress."""
    path = get_progress_path(book_id)
    path.write_text(json.dumps({"page": page, "total": total}))


def load_progress(book_id: str) -> Optional[int]:
    """Load saved progress, returns page number or None."""
    path = get_progress_path(book_id)
    if path.exists():
        try:
            data = json.loads(path.read_text())
            return data.get("page", 0)
        except (json.JSONDecodeError, KeyError):
            return None
    return None


def read_char() -> str:
    """Read a single character without requiring Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def read_book(
    get_page: Callable[[int, int], tuple[str, int]],
    title: str,
    author: str = "",
    book_id: str = "",
    get_chapters: Optional[Callable[[], list]] = None,
):
    """Interactive reading loop."""
    page = 0
    total = 1

    # Load saved progress
    if book_id:
        saved_page = load_progress(book_id)
        if saved_page is not None:
            page = saved_page
            print(f"[继续上次阅读: 第 {page + 1} 页]")

    def show_page(book, page_num):
        """Show a single page, skipping blank pages."""
        content, total = get_page(page_num, 0)
        if content.strip():
            return content, total, page_num
        # Skip blank pages
        if page_num < total - 1:
            return show_page(book, page_num + 1)
        else:
            return "", total, page_num

    while True:
        content, total, actual_page = show_page(None, page)

        if not content:
            print("\n[已到末尾]")
            break

        # Clear screen and show content
        os.system('clear' if os.name != 'nt' else 'cls')
        print(f"《{title}》 {author}")
        print("=" * 50)

        # Show 30 lines per page
        lines = content.split("\n")
        for line in lines[:30]:
            print(line)

        print("-" * 50)
        print(f"[第 {actual_page + 1}/{total} 页] | n=下一页 p=上一页 g=跳转 c=目录 q=退出")
        print("\n请按键操作...", end="", flush=True)

        cmd = read_char()
        print()  # New line after keypress

        if cmd == "q" or cmd == "Q":
            if book_id:
                save_progress(book_id, page, total)
            print("已退出，阅读进度已保存。")
            break
        elif cmd == "n" or cmd == "\r" or cmd == "\n" or cmd == "\x03":  # n, Enter, or Ctrl+C
            if cmd in ("\r", "\n"):
                cmd = "n"  # Treat Enter as next
            if page < total - 1:
                page += 1
                if book_id:
                    save_progress(book_id, page, total)
        elif cmd == "p" or cmd == "P":
            if page > 0:
                page -= 1
                if book_id:
                    save_progress(book_id, page, total)
        elif cmd == "g" or cmd == "G":
            # Jump to page
            print("跳转页码: ", end="", flush=True)
            num_str = ""
            while True:
                c = read_char()
                if c == "\r" or c == "\n":
                    break
                elif c == "\x03":  # Ctrl+C
                    break
                elif c == "\x7f":  # Backspace
                    if num_str:
                        num_str = num_str[:-1]
                        print("\b \b", end="", flush=True)
                else:
                    num_str += c
                    print(c, end="", flush=True)
            print()
            if num_str.isdigit():
                target = int(num_str) - 1
                if 0 <= target < total:
                    page = target
                    if book_id:
                        save_progress(book_id, page, total)
                else:
                    print(f"页码无效，范围: 1-{total}")
            elif num_str:
                print("请输入有效数字")
        elif cmd == "c" or cmd == "C":
            if get_chapters:
                # Show chapters
                chapters = get_chapters()
                os.system('clear' if os.name != 'nt' else 'cls')
                print(f"《{title}》目录")
                print("=" * 50)
                for i, ch in enumerate(chapters):
                    print(f"  {i + 1}. {ch.title}")
                print("-" * 50)
                print(f"共 {len(chapters)} 章 | 输入章节编号跳转")
                print("\n选择章节: ", end="", flush=True)
                num_str = ""
                while True:
                    c = read_char()
                    if c == "\r" or c == "\n":
                        break
                    elif c == "\x03":  # Ctrl+C
                        break
                    elif c == "\x7f":  # Backspace
                        if num_str:
                            num_str = num_str[:-1]
                            print("\b \b", end="", flush=True)
                    else:
                        num_str += c
                        print(c, end="", flush=True)
                print()
                if num_str.isdigit():
                    choice = int(num_str)
                    if 1 <= choice <= len(chapters):
                        page = int(chapters[choice - 1].chapter_id)
                        if book_id:
                            save_progress(book_id, page, total)
                    else:
                        print("无效选择")
            else:
                print("[该书无目录]")
        elif cmd == "\x03":  # Ctrl+C
            if book_id:
                save_progress(book_id, page, total)
            print("已退出 (Ctrl+C)，阅读进度已保存。")
            break


def clear_progress(book_id: str):
    """Clear saved progress for a book."""
    path = get_progress_path(book_id)
    if path.exists():
        path.unlink()
        print("进度已清除")
    else:
        print("无保存的进度")
