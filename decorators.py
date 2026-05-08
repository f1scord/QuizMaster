# decorators — we need at least one custom decorator (3 pts)
import functools
import traceback
from datetime import datetime


def log_action(func):
    """logs every call to a function with timestamp"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # write to log file using context manager (with statement)
        with open("logs.txt", "a", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().isoformat(timespec='seconds')}] {func.__name__}\n"
            )
        return func(*args, **kwargs)

    return wrapper


def handle_errors(func):
    """catches our custom errors and shows them in a popup"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import tkinter.messagebox as mb

        from exceptions import FlashcardsError

        try:
            return func(*args, **kwargs)
        except FlashcardsError as e:
            mb.showerror("flashcards error", str(e))
        except Exception:
            tb = traceback.format_exc()
            with open("logs.txt", "a", encoding="utf-8") as f:
                f.write(
                    f"[{datetime.now().isoformat(timespec='seconds')}] UNHANDLED:\n{tb}\n"
                )
            mb.showerror("unexpected error", "something went wrong. check logs.txt")

    return wrapper
