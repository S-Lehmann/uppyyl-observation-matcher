"""This module implements a CLI for the Uppaal Simulator."""

import argparse
import glob
import os
import pprint
import re
import readline
from ast import literal_eval
from cmd import Cmd
from enum import Enum

from colorama import Fore

from uppaal_c_language.backend.parsers.generated.uppaal_c_language_parser import UppaalCLanguageParser
from uppaal_c_language.backend.parsers.uppaal_c_language_semantics import UppaalCLanguageSemantics

readline.set_completer_delims(' \t\n')

pp = pprint.PrettyPrinter(indent=4, compact=True)
printExpectedResults = False
printActualResults = False


##############################
# Helper Classes and Objects #
##############################
class ArgumentParserError(Exception):
    """Exception raised for argument parsing errors."""
    pass


class ArgumentParser(argparse.ArgumentParser):
    """A helper subclass of argparse.ArgumentParser that disables exiting the program on parsing errors."""

    def error(self, message):
        """The overwritten error function which is called when an argument parsing error occurs.

        Args:
            message: The error message.
        """
        usage = self.format_usage()[:-1]
        raise ArgumentParserError(f'{message} ({usage})')


load_parser = ArgumentParser(prog='load', add_help=False)
load_parser.add_argument('filepath', metavar='filepath')

transition_pattern = re.compile(r't(\d+)')


class View(Enum):
    """An enum for the possible graphical views."""
    UPPAAL_C_TO_AST = 1


def _complete_path(path):
    if os.path.isdir(path):
        return False, glob.glob(os.path.join(path, '*'))
    else:
        return True, glob.glob(path + '*')


#######################
# Uppaal C Parser CLI #
#######################
class UppaalCLanguageCLI(Cmd):
    """A CLI for the Uppaal C Parser."""

    prompt = 'uppyyl_c_parser> '
    intro = ""

    def __init__(self):
        """Initializes UppaalCLanguageCLI."""
        super(UppaalCLanguageCLI, self).__init__()
        self.uppaal_c_parser = UppaalCLanguageParser(semantics=UppaalCLanguageSemantics())
        self.active_view = View.UPPAAL_C_TO_AST
        self.recent_input = ""
        self.recent_ast = {}

        help_message = "This is the Uppaal C Parser CLI. Type ? to list commands."
        self.print_view(message=help_message)

    def print_view(self, message=""):
        """Prints the view.

        Args:
            message: An optional information message.
        """
        view_string = self.get_view_string()

        self.clear()
        print(f'{Fore.BLUE}Message:{Fore.RESET} {message}')
        print(f'\n--| {Fore.BLUE}AST for "{self.recent_input}"{Fore.RESET} |----------------------------')
        print(view_string)
        print(f'')

    def get_view_string(self):
        """Constructs the string representation of the view.

        Returns:
            The trace string.
        """
        return pp.pformat(self.recent_ast)

    @staticmethod
    def do_exit(_arg=None):
        """Performs the "exit" command."""
        return True

    @staticmethod
    def help_exit():
        """Shows help for the "exit" command."""
        print('Exits the application. Shorthand: x, q, or Ctrl-D.')

    @staticmethod
    def clear():
        """Clears the console."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def emptyline(self):
        """Performs an empty command."""
        self.print_view(message=f'')

    def default(self, inp):
        """Performs a "default" command (i.e., no specific "do_..." function exists)."""
        # Exit
        if inp == 'x' or inp == 'q':
            return self.do_exit()
        else:
            text, rule_name = literal_eval(inp)
            ast = self.uppaal_c_parser.parse(text=text, rule_name=rule_name)
            self.recent_input = text
            self.recent_ast = ast

        self.print_view(message=f'')

    do_EOF = do_exit
    help_EOF = help_exit
