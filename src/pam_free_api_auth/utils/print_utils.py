from pam_free_api_auth import colors

def add_padding(text, amount=1):
    """
    Adds spaces around the text.

    :param (str) text: The text that the spaces will be added to.
    :param (int) amount: Amount of spaces to add.
    :return (str): New string with spaces.
    """
    padding = " " * amount
    return padding + text + padding


def print_header(header_text, header_color=colors.GREEN):
    """
    Prints a header:
        === Header ===

    :param (str) header_text: The header title.
    :param (str) header_color: The color of the header.
    """
    if len(header_text) > 0:
        header_text = add_padding(header_text)
    print header_color + "\n===" + header_text + "===\n" + colors.ENDC


def print_section(text, text_color=colors.BLUE, header_text="", header_color=colors.GREEN):
    """
    Prints a section with header and text:
        === Header ===
            This is a section content

    :param (str) text: The section text.
    :param (str) text_color: The color of the section text.
    :param (str) header_text: The header title.
    :param (str) header_color: The color of the header.
    """
    text = text.replace("\n", "\n\t")

    print_header(header_text=header_text, header_color=header_color)
    print text_color + "\t" + text + colors.ENDC
