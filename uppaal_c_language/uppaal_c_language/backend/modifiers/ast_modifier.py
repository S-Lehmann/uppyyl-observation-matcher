"""This module implements modifiers for Uppaal C ASTs."""
import re


class ASTModifier:
    """This class provides the modifiers for Uppaal C ASTs."""

    def __init__(self):
        """Initializes ASTModifier."""
        pass

    @staticmethod
    def rename_variable(ast, orig_name, new_name):
        """Renames each occurrence of a variable.

        Args:
            ast: The target AST in which the variable should be renamed.
            orig_name: The original variable name.
            new_name: The new variable name.

        Returns:
            The resulting AST.
        """
        pass  # TODO

    @staticmethod
    def adapt_variable_value_in_declaration(ast, var_name, val):
        """Adapts target value(s) assigned to a variable during declaration.

        Args:
            ast: The target AST in which variable values should be adapted.
            var_name: The target variable name. If the variable name contains (partial) indices, the values are assigned
                      to the corresponding sub-list(s).
                      E.g., for an array arr[3][3][3], val=[1,2,3] and var_name=arr[2][2] sets
                        arr[2][2][0] = 1, arr[2][2][1] = 2, and arr[2][2][2] = 3.
            val: The new variable value.

        Returns:
            The resulting AST.
        """

        # Check if variable name contains array indexing
        var_base_name, index_part = re.search(r'(\w+)?((?:\[\d+])*)$', var_name).groups()
        if index_part:
            indices = list(map(lambda i: int(i[1]), re.findall(r'(\[(\d)+])', index_part)))
        else:
            indices = []

        def local_var_adapt_func(curr_ast, acc):
            """Helper function for variable name adaption."""

            # Replace variable value in declarations
            if curr_ast["astType"] == 'VariableDecls':
                for single_var_data in curr_ast["varData"]:
                    if single_var_data["varName"] == var_base_name:
                        if not indices:
                            single_var_data["initData"] = value_data_to_ast(val)
                        else:
                            init_data = single_var_data["initData"]
                            for index in indices[:-1]:
                                init_data = init_data["vals"][index]
                            init_data["vals"][indices[-1]] = value_data_to_ast(val)
                        if len(acc) == 0:
                            acc.append(True)

            # # Replace variable value in assignments in "init" function
            # elif curr_ast["astType"] == 'Function' and curr_ast["name"] == 'initialize':
            #     for stmt in curr_ast["body"]["stmts"]:
            #         if stmt["astType"] == "ExprStatement" and stmt["expr"]["astType"] == 'AssignExpr':
            #             stmt["expr"]["right"] = value_data_to_ast(val)
            return curr_ast

        new_ast, acc_res = apply_func_to_ast(ast=ast, func=local_var_adapt_func)
        if not acc_res:
            print(f'Variable "{var_name}" NOT found.')
        # else:
        #     print(f'Variable "{var_name}" found and its value replaced.')
        return new_ast


########################################################################################################################

def atomic_value_to_ast(val):
    """Transforms an atomic value into the corresponding AST.

    Args:
        val: The atomic value.

    Returns:
        The generated AST.
    """
    if isinstance(val, bool):
        return {"astType": "Boolean", "val": val}
    elif isinstance(val, int):
        return {"astType": "Integer", "val": val}
    elif isinstance(val, float):
        return {"astType": "Double", "val": val}
    raise Exception("Unknown atomic value type. Abort.")


def value_data_to_ast(val):
    """Transforms value data (i.e., atomic value or list) into the corresponding AST.

    Args:
        val: The value data.

    Returns:
        The generated AST.
    """
    if isinstance(val, list):
        # ast_vals = list(map(atomic_value_to_ast, val))
        ast_vals = list(map(value_data_to_ast, val))
        ast = {"astType": "InitialiserArray", "vals": ast_vals}
    else:
        ast = atomic_value_to_ast(val)
    return ast


########################################################################################################################

def apply_func_to_ast(ast, func):
    """Applies a function recursively to all (nested) elements of an AST.

    Args:
        ast: The AST instance.
        func: The function applied to the AST elements.

    Returns:
        The adapted AST and values accumulated during application.
    """
    acc = []
    ast = apply_func_to_ast_helper(ast, func, acc)
    return ast, acc


def apply_func_to_ast_helper(ast, func, acc):
    """Recursive helper function for "apply_func_to_ast".

    Args:
        ast: The AST instance.
        func: The function applied to the AST elements.
        acc: A list of values accumulated during application.

    Returns:
        The adapted AST.
    """
    if isinstance(ast, dict):  # If val is AST
        for prop_name, prop_val in ast.items():
            ast[prop_name] = apply_func_to_ast_helper(prop_val, func, acc)
        ast = func(ast, acc)
    elif isinstance(ast, list):  # If val is List
        for i in range(0, len(ast)):
            ast[i] = apply_func_to_ast_helper(ast[i], func, acc)
    return ast


def apply_funcs_to_ast(ast, funcs):
    """Applies multiple functions simultaneously to all (nested) elements of an AST.

    Args:
        ast: The AST instance.
        funcs: A list of functions applied to the AST elements simultaneously.

    Returns:
        The adapted AST.
    """

    def helper_func(ast_, _acc):
        """Helper function which applies the given functions to the AST.

        Args:
            ast_: The AST instance.
            _acc: A list of values accumulated during application.

        Returns:
            The adapted AST.
        """
        for func in funcs:
            ast_ = func(ast_, _acc)
        return ast_

    return apply_func_to_ast(ast, helper_func)
