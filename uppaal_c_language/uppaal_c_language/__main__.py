"""The main entry point of the Uppaal C language module."""
import argparse

from uppaal_c_language.frontend.cli import UppaalCLanguageCLI


def parse_arguments():
    """Parses the main input arguments.

    Returns:
        The parsed input arguments.
    """
    parser = argparse.ArgumentParser(description='The Uppaal C language parser.')
    args = parser.parse_args()
    return vars(args)


def main():
    """The main function."""
    # args = parse_arguments()
    prompt = UppaalCLanguageCLI()
    prompt.cmdloop()


if __name__ == '__main__':
    main()
