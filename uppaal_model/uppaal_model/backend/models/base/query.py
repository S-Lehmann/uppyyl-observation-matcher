"""This module implements a wrapper class for Uppaal verification queries."""

import copy

from uppaal_model.backend.ast_code_element import ASTCodeElement
from uppaal_c_language.backend.parsers.generated.uppaal_c_language_parser import UppaalCLanguageParser
from uppaal_c_language.backend.parsers.uppaal_c_language_semantics import UppaalCLanguageSemantics
from uppaal_c_language.backend.printers.uppaal_query_language_printer import UppaalQueryPrinter


#########
# Query #
#########
class Query:
    """A representation of Uppaal query."""

    def __init__(self, formula, comment):
        """Initializes Query.

        Args:
            formula: The query formula string (e.g., A[] phi)
            comment: An optional comment for the query.
        """
        self.formula = None
        self.set_formula(formula)
        self.comment = comment

    def set_formula(self, formula):
        """Sets the formula of the query object.

        Args:
            formula: The formula object or string.

        Returns:
            The formula object.
        """
        if isinstance(formula, str):
            formula = QueryFormula(formula)
        self.formula = formula
        return formula

    def copy(self):
        """Copies the QueryFormula instance.

        Returns:
            The copied QueryFormula instance.
        """
        copy_query = Query(formula=self.formula.copy(), comment=self.comment)
        return copy_query


#################
# Query Formula #
#################
class QueryFormula(ASTCodeElement):
    """A representation of Uppaal query formula."""

    def __init__(self, formula_data):
        """Initializes QueryFormula.

        Args:
            formula_data: The formula data string or AST dict.
        """
        super().__init__(formula_data)

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
        self.printer = UppaalQueryPrinter()

    def copy(self):
        """Copies the QueryFormula instance.

        Returns:
            The copied QueryFormula instance.
        """
        copy_formula = QueryFormula(copy.deepcopy(self.ast))
        return copy_formula

    def update_ast(self):
        """Updates the AST dict from the AST text string.

        Returns:
            None
        """
        if not self.text:
            self.ast = None
        else:
            self.ast = self.parser.parse(self.text, rule_name='UppaalProp', trace=False)

    def __str__(self):
        return f'QueryFormula(\n{self.text}\n)'
