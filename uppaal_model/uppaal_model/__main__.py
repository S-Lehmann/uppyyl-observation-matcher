"""The main entry point of the Uppaal model module."""

import argparse


def parse_arguments():
    """Parses the main input arguments.

    Returns:
        The parsed input arguments.
    """
    parser = argparse.ArgumentParser(description='The Uppaal model parser.')
    args = parser.parse_args()
    return vars(args)


def main():
    """The main function."""
    # args = parse_arguments()
    # prompt = UppaalModelCLI()
    # prompt.cmdloop()


if __name__ == '__main__':
    main()
