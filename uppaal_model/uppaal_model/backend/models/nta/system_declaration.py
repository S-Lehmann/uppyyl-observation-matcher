"""The system declaration (i.e., which instances should be created and composed) of an Uppaal automaton network."""

import copy

from uppaal_model.backend.ast_code_element import ASTCodeElement
from uppaal_c_language.backend.parsers.generated.uppaal_c_language_parser import UppaalCLanguageParser
from uppaal_c_language.backend.parsers.uppaal_c_language_semantics import UppaalCLanguageSemantics
from uppaal_c_language.backend.printers.uppaal_c_language_printer import UppaalCPrinter


######################
# System Declaration #
######################
class SystemDeclaration(ASTCodeElement):
    """A system declaration class.

    In the system declaration, template instances are defined and composed into a system.
    """

    def __init__(self, decl_data):
        """Initializes SystemDeclaration.

        Args:
            decl_data: The system declaration string or AST data.
        """
        super().__init__(decl_data)

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
        """Copies the SystemDeclaration instance.

        Returns:
            The copied SystemDeclaration instance.
        """
        copy_decl = SystemDeclaration(copy.deepcopy(self.ast))
        return copy_decl

    def update_ast(self):
        """Updates the AST dict from the AST text string.

        Returns:
            None
        """
        if not self.text:
            self.ast = {
                "astType": 'UppaalSystemDeclaration',
                "decls": [],
                "systemDecl": {"astType": "System", "processNames": [[]]}
            }
        else:
            self.ast = self.parser.parse(self.text, rule_name='UppaalSystemDeclaration')

    def __str__(self):
        return f'SystemDeclaration(\n{self.text}\n)'
