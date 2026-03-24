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
