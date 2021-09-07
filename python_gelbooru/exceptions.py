class GelbooruError(Exception):
    """
    The base exception for Gelbooru Exceptions
    """
    pass


class GelbooruLimitError(GelbooruError):
    """
    Exception raised when the amount of posts you are trying to grab is too large
    """
    pass