# custom exceptions for the app
# we need at least one custom exception for the project (2 pts)


class FlashcardsError(Exception):
    """base error for our app"""

    pass


class ApiError(FlashcardsError):
    """raised when something goes wrong with the ai api"""

    pass


class FileNotSupportedError(FlashcardsError):
    """raised when user tries to open a file we cant read"""

    pass


class StorageError(FlashcardsError):
    """raised when saving or loading fails"""

    pass
