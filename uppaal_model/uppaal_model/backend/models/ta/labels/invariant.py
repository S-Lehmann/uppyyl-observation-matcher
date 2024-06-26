"""The invariant label of an Uppaal automaton location."""

import copy

from uppaal_model.backend.ast_code_element import ASTCodeElement
from uppaal_c_language.backend.parsers.generated.uppaal_c_language_parser import UppaalCLanguageParser
from uppaal_c_language.backend.parsers.uppaal_c_language_semantics import UppaalCLanguageSemantics
from uppaal_c_language.backend.printers.uppaal_c_language_printer import UppaalCPrinter


#############
# Invariant #
#############
class Invariant(ASTCodeElement):
    """A location invariant class.

    Via an invariant, a condition on a clock variable is enforced.
    """

    def __init__(self, inv_data, autom=None):
        """Initializes Invariant.

        Args:
            inv_data: The location invariant string or AST data.
        """
        super().__init__(inv_data)
        self.autom = autom

    def init_parser(self):
        """Initializes the AST code parser.

        Returns:
            None
        """
        self.parser = UppaalCLanguageParser(semantics=UppaalCLanguageSemantics())

    def init_printer(self):
        """Initializes the AST code printer.

         Returns:
             None
         """
        self.printer = UppaalCPrinter()

    def copy(self):
        """Copies the Invariant instance.

        Returns:
            The copied Invariant instance.
        """
        copy_inv = Invariant(copy.deepcopy(self.ast))
        return copy_inv

    def update_ast(self):
        """Updates the AST dict from the AST text string.

        Returns:
            None
        """
        self.ast = self.parser.parse(self.text, rule_name='Invariant')

    def __str__(self):
        return f'Invariant({self.text})'
