import functools
import traceback
from datetime import datetime


def log_action(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        summary = f"{func.__name__}({str(args[1:])[:80]})"
        with open("logs.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat(timespec='seconds')}] {summary}\n")
        return func(*args, **kwargs)
    return wrapper


def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import tkinter.messagebox as mb
        from exceptions import QuizMasterError
        try:
            return func(*args, **kwargs)
        except QuizMasterError as e:
            mb.showerror("QuizMaster error", str(e))
        except Exception:
            tb = traceback.format_exc()
            with open("logs.txt", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat(timespec='seconds')}] UNHANDLED:\n{tb}\n")
            mb.showerror("Unexpected error", "Something went wrong. Check logs.txt for details.")
    return wrapper
