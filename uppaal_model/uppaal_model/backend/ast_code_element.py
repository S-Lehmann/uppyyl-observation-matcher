"""Abstract class for an AST code element."""

import abc


class ASTCodeElement(abc.ABC):
    """An abstract AST code element."""

    def __init__(self, data):
        """Initializes ASTCodeElement.

        Args:
            data: The AST data in string form or as AST dict.
        """
        self.printer = None
        self.parser = None
        self.init_parser()
        self.init_printer()

        self.text = None
        self.ast = None
        if isinstance(data, str):
            self.set_text(data)
        else:
            self.set_ast(data)

    @abc.abstractmethod
    def init_parser(self):
        """Initializes the AST code parser.

        Returns:
            None
        """

    @abc.abstractmethod
    def init_printer(self):
        """Initializes the AST code printer.

        Returns:
            None
        """

    def update_text(self):
        """Updates the AST text string from the AST dict.

        Returns:
            None
        """
        self.text = self.printer.ast_to_string(self.ast)

    @abc.abstractmethod
    def update_ast(self):
        """Updates the AST dict from the AST text string.

        Returns:
            None
        """

    def set_text(self, text):
        """Sets the AST text string, and update the AST dict accordingly.

        Returns:
            None
        """
        self.text = text if (text is not None) else ""
        self.update_ast()

        # if text == "":
        #     self.ast = None
        # else:
        #     self.update_ast()

    def set_ast(self, ast):
        """Sets the AST dict, and update the AST text string accordingly.

        Returns:
            None
        """
        self.ast = ast
        self.update_text()

    @abc.abstractmethod
    def copy(self):
        """Copies the ASTCodeElement instance.

        Returns:
            The copied ASTCodeElement instance.
        """
