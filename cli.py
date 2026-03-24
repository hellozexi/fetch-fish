"""fetch-fish CLI entry point."""
import argparse
import sys
import config
from providers.pdf import PDFBook
from providers.weread import WeReadBook
from reader import read_book


def cmd_weread_list(args):
    """List WeRead books from cache."""
    from storage.cache import get_db, init_db
    init_db()
    db = get_db()
    books = db.execute("SELECT id, title, author FROM books").fetchall()
    if not books:
        print("No books cached. Run 'weread sync' first.")
        return
    for b in books:
        print(f"{b['id']}  {b['title']} - {b['author']}")


def cmd_weread_read(args):
    """Read a WeRead book."""
    book = WeReadBook(book_id=args.book_id)
    read_book(book.get_page, book.title, book.author)


def cmd_weread_sync(args):
    """Sync WeRead books from API to cache."""
    from storage.cache import init_db
    init_db()
    book = WeReadBook(book_id="")
    try:
        book.cache_books()
        print("Books synced successfully.")
    except Exception as e:
        print(f"Sync failed: {e}")


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
    weread_sub = p_weread.add_subparsers()
    weread_sub.add_parser("list", help="List cached books").set_defaults(func=cmd_weread_list)
    weread_sub.add_parser("sync", help="Sync books from WeRead API").set_defaults(func=cmd_weread_sync)
    p_weread_read = weread_sub.add_parser("read", help="Read a book")
    p_weread_read.add_argument("book_id")
    p_weread_read.set_defaults(func=cmd_weread_read)

    # PDF command
    p_pdf = sub.add_parser("pdf", help="PDF commands")
    pdf_sub = p_pdf.add_subparsers()
    p_pdf_open = pdf_sub.add_parser("open", help="Open PDF")
    p_pdf_open.add_argument("path")
    p_pdf_open.set_defaults(func=cmd_pdf_open)

    # Config command
    p_config = sub.add_parser("config", help="Configuration")
    config_sub = p_config.add_subparsers()
    p_set_cookie = config_sub.add_parser("set-cookie", help="Set WeRead cookie")
    p_set_cookie.add_argument("cookie")
    p_set_cookie.set_defaults(func=cmd_set_cookie)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
