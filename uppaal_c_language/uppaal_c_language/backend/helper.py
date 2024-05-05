"""A module with several helper functions."""


def prepend_to_lines(text, prepend_str):
    """Prepends a string to every line of a given text.

    Args:
        text: The text whose lines the string is prepended to.
        prepend_str: The prepended string.

    Returns:
        The text with each line prepended by string.
    """
    return '\n'.join(map(lambda x: prepend_str + x, text.split('\n')))


def indent(text, space_num):
    """Indents each line of a text by a given amount of whitespace characters.

    Args:
        text: The text whose lines the whitespaces are prepended to.
        space_num: The number of whitespaces for indentation.

    Returns:
        The indented text.
    """
    return prepend_to_lines(text, " " * space_num)
