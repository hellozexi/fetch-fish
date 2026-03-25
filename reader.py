"""Interactive CLI reader."""
import json
import os
from pathlib import Path
from typing import Callable, Optional

PROGRESS_DIR = Path.home() / ".fetch-fish" / "progress"
PROGRESS_DIR.mkdir(parents=True, exist_ok=True)


def get_progress_path(book_id: str) -> Path:
    """Get progress file path for a book."""
    # Use hash of book_id to create filename
    import hashlib
    h = hashlib.md5(book_id.encode()).hexdigest()[:12]
    return PROGRESS_DIR / f"{h}.json"


def save_progress(book_id: str, page: int, total: int):
    """Save reading progress."""
    path = get_progress_path(book_id)
    path.write_text(json.dumps({"page": page, "total": total}))
    print(f"\033[2K\r  [进度已保存: 第 {page + 1}/{total} 页]", end="", flush=True)


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
    page_size = 500

    # Load saved progress
    if book_id:
        saved_page = load_progress(book_id)
        if saved_page is not None:
            page = saved_page
            print(f"[继续上次阅读: 第 {page + 1} 页]")

    while True:
        content, total = get_page(page, page_size)
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
        print(f"[第 {page + 1}/{total} 页] | n=下一页 p=上一页 g=跳转 c=目录 q=退出")

        cmd = input("\n命令: ").strip().lower()

        if cmd == "q":
            if book_id:
                save_progress(book_id, page, total)
            print("\n已退出，阅读进度已保存。")
            break
        elif cmd == "n" or cmd == "":
            if page < total - 1:
                page += 1
                if book_id:
                    save_progress(book_id, page, total)
        elif cmd == "p":
            if page > 0:
                page -= 1
                if book_id:
                    save_progress(book_id, page, total)
        elif cmd == "g":
            # Jump to page
            try:
                target = int(input("跳转页码: ").strip()) - 1
                if 0 <= target < total:
                    page = target
                    if book_id:
                        save_progress(book_id, page, total)
                else:
                    print(f"页码无效，范围: 1-{total}")
            except ValueError:
                print("请输入有效数字")
        elif cmd == "c" and get_chapters:
            # Show chapters
            chapters = get_chapters()
            os.system('clear' if os.name != 'nt' else 'cls')
            print(f"《{title}》目录")
            print("=" * 50)
            for i, ch in enumerate(chapters):
                print(f"  {i + 1}. {ch.title}")
            print("-" * 50)
            print(f"共 {len(chapters)} 章 | 输入章节编号跳转")

            try:
                choice = int(input("\n选择章节: ").strip())
                if 1 <= choice <= len(chapters):
                    page = int(chapters[choice - 1].chapter_id)
                    if book_id:
                        save_progress(book_id, page, total)
                else:
                    print("无效选择")
            except ValueError:
                print("请输入有效数字")
        elif cmd == "c" and not get_chapters:
            print("[该书无目录]")


def clear_progress(book_id: str):
    """Clear saved progress for a book."""
    path = get_progress_path(book_id)
    if path.exists():
        path.unlink()
        print("进度已清除")
    else:
        print("无保存的进度")
