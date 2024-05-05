"""This module implements modifiers for Uppaal NTA systems."""

import copy
import pprint

from uppaal_c_language.backend.modifiers.ast_modifier import apply_func_to_ast
from uppaal_c_language.backend.parsers.generated.uppaal_c_language_parser import UppaalCLanguageParser
from uppaal_c_language.backend.parsers.uppaal_c_language_semantics import UppaalCLanguageSemantics
from uppaal_c_language.backend.printers.uppaal_c_language_printer import UppaalCPrinter

##################
# SystemModifier #
##################
from uppaal_model.backend.models.ta.modifiers.ta_modifier import TemplateModifier


class SystemModifier:
    """This class provides modifiers for Uppaal NTA systems."""

    def __init__(self):
        """Initializes SystemModifier."""
        pass

    @staticmethod
    def move_sys_vars_to_global_decl(system):
        """Moves all variable declarations in the system declaration section to the global declaration.

        Args:
            system: The system object.

        Returns:
            None
        """

        system_decl_stmts = system.system_declaration.ast["decls"]
        global_decl_stmts = system.declaration.ast["decls"]
        i = 0
        while i < len(system_decl_stmts):
            system_stmt = system_decl_stmts[i]
            if (system_stmt["astType"] == "VariableDecls" or system_stmt["astType"] == "TypeDecls"
                    or system_stmt["astType"] == "Function"):
                global_decl_stmts.append(system_stmt)
                del system_decl_stmts[i]
                continue
            i += 1
        system.declaration.update_text()
        system.system_declaration.update_text()

    @staticmethod
    def convert_instances_to_templates(system, instance_data, keep_original_templates=True):
        """Generate a template for each automata instance (optionally keep original templates).

        Args:
            system: The system object
            instance_data: The template and argument data of all instances
            keep_original_templates: Defines whether the original templates should be kept or not

        Returns:

        """
        # Make all instances explicit (e.g., implicit template instances based on bounded integer ID ranges)
        template_names = [tmpl.name for tmpl in system.templates.values()]
        process_names = system.system_declaration.ast["systemDecl"]["processNames"]
        updated_process_names = []
        for process_block in process_names:
            updated_process_block = []
            for process_name in process_block:
                if process_name in template_names:
                    for proc_name, proc_data in instance_data.items():
                        if proc_data["template_name"] == process_name:
                            updated_process_block.append(proc_name)
                else:
                    updated_process_block.append(process_name)
            updated_process_names.append(updated_process_block)
        system.system_declaration.ast["systemDecl"]["processNames"] = updated_process_names

        # Remove original instantiations from system declaration AST
        system_decl_stmts = system.system_declaration.ast["decls"]
        i = 0
        while i < len(system_decl_stmts):
            system_stmt = system_decl_stmts[i]
            if system_stmt["astType"] == 'Instantiation':
                del system_decl_stmts[i]
                continue
            i += 1

        # Replace scalars by integers
        for decl in system.declaration.ast["decls"]:
            # print(decl)
            if decl["astType"] in ["TypeDecls", "VariableDecls"] and decl["type"]["typeId"]["astType"] == "ScalarType":
                decl["type"]["typeId"] = {
                    'astType': 'BoundedIntType',
                    'lower': {'val': 0, 'astType': 'Integer'},
                    'upper': {
                        'left': decl["type"]["typeId"]["expr"],
                        'op': 'Sub',
                        'right': {'val': 1, 'astType': 'Integer'},
                        'astType': 'BinaryExpr'
                    },
                }

        # Create templates based on instance data
        old_instance_templates = {}
        # new_instance_templates = {}
        new_instance_data = {}
        for inst_name, inst_data in instance_data.items():
            tmpl_name = inst_data["template_name"]
            args = inst_data["args"]
            ref_tmpl = system.get_template_by_name(tmpl_name)
            old_instance_templates[inst_name] = ref_tmpl

            new_tmpl_name = f'{inst_name}_Tmpl'
            new_tmpl = system.new_template(new_tmpl_name)
            new_tmpl.assign_from(ref_tmpl)
            system.templates[new_tmpl.id] = new_tmpl

            # new_instance_templates[inst_name] = new_tmpl

            # Add template as instance of system declaration
            instantiation_ast = {
                "astType": 'Instantiation',
                "instanceName": inst_name,
                "params": [],
                "templateName": new_tmpl_name,
                "args": copy.deepcopy(args)
            }
            system_decl_stmts.append(instantiation_ast)
            new_instance_data[inst_name] = instantiation_ast

        system.system_declaration.update_text()

        if not keep_original_templates:
            old_tmpls = set(old_instance_templates.values())
            for old_tmpl in old_tmpls:
                del system.templates[old_tmpl.id]

        return new_instance_data

    @staticmethod
    def resolve_parameters(system, tmpl):
        SystemModifier.replace_call_by_reference_parameters(system=system, tmpl=tmpl)
        SystemModifier.move_call_by_value_parameters_to_local_declaration(system=system, tmpl=tmpl)

    # @staticmethod
    # def convert_local_vars_to_global_vars(system, tmpl, args):
    #     """Convert all local template variables to global ones (requires at most one instance per template).
    #
    #     Args:
    #         system: The system object
    #         tmpl: The template from which all variables should be moved to the global declaration
    #         args: The argument data of the template instance
    #
    #     Returns:
    #         None
    #     """
    #     args = instance_data["args"]
    #     SystemModifier.replace_call_by_reference_parameters(tmpl=tmpl, args=args)
    #     SystemModifier.move_call_by_value_parameters_to_local_declaration(tmpl=tmpl, args=args)
    #     SystemModifier.convert_local_decl_to_global_decl(system=system, tmpl=tmpl)

    @staticmethod
    def convert_local_decl_to_global_decl(system, tmpl):
        """Convert all local template declaration variables to global ones.
        Note: Before applying, ensure that each template is instantiated at most once.

        Args:
            system: The system object
            tmpl: The template from which all variables should be moved to the global declaration
            args: The argument data of the template instance

        Returns:
            None
        """
        if isinstance(tmpl, str):
            tmpl = system.get_template(tmpl)

        local_var_names = []
        local_type_names = []
        local_func_names = []

        # Extract variable declarations from local declaration text
        stmts = tmpl.declaration.ast["decls"]
        for i in range(0, len(stmts)):
            stmt = stmts[i]
            if stmt["astType"] == "VariableDecls":
                for single_var_id in stmt["varData"]:
                    local_var_names.append(single_var_id["varName"])
            elif stmt["astType"] == "Function":
                local_func_names.append(stmt["name"])
            elif stmt["astType"] == "TypeDecls":
                for type_name_id in stmt["names"]:
                    local_type_names.append(type_name_id["varName"])

        # Copy local ast
        new_global_ast_part = copy.deepcopy(tmpl.declaration.ast)

        # Replace all locally defined variables, types and functions with their global counterparts
        for i in range(0, len(local_var_names)):
            def local_var_adapt_func(ast, _acc):
                """Helper function for variable name adaption."""
                if ast["astType"] == 'VariableID' and ast["varName"] == local_var_names[i]:
                    ast["varName"] = f'{tmpl.name}_{local_var_names[i]}'
                elif ast["astType"] == 'Variable' and ast["name"] == local_var_names[i]:
                    ast["name"] = f'{tmpl.name}_{local_var_names[i]}'
                return ast

            new_global_ast_part, _ = apply_func_to_ast(ast=new_global_ast_part, func=local_var_adapt_func)
            # pprint.pprint(new_global_ast_part, indent=2)

        for i in range(0, len(local_func_names)):
            def local_func_adapt_func(ast, _acc):
                """Helper function for function name adaption."""
                if ast["astType"] == 'FuncDef' and ast["name"] == local_func_names[i]:
                    ast["varName"] = f'{tmpl.name}_{local_func_names[i]}'
                return ast

            new_global_ast_part, _ = apply_func_to_ast(ast=new_global_ast_part, func=local_func_adapt_func)

        for i in range(0, len(local_type_names)):
            def local_type_adapt_func(ast, _acc):
                """Helper function for type name adaption."""
                if ast["astType"] == 'CustomType' and ast["type"] == local_type_names[i]:
                    ast["type"] = f'{tmpl.name}_{local_type_names[i]}'
                return ast

            new_global_ast_part, _ = apply_func_to_ast(ast=new_global_ast_part, func=local_type_adapt_func)

        # Insert new global AST part into global declaration ast
        system.declaration.ast["decls"].extend(new_global_ast_part["decls"])

        # Update variables inside model
        var_replacements = []
        for i in range(0, len(local_var_names)):
            def model_var_adapt_func(old_name, new_name):
                """Helper function for name adaption."""

                def ast_func(ast, _acc):
                    """Helper function for name adaption."""
                    if ast["astType"] == 'Variable' and ast["name"] == old_name:
                        ast["name"] = new_name
                    return ast

                return ast_func

            old_name_ = local_var_names[i]
            new_name_ = f'{tmpl.name}_{old_name_}'

            var_replacements.append(model_var_adapt_func(old_name=old_name_, new_name=new_name_))

        TemplateModifier.adapt_asts(tmpl=tmpl, adaptions=var_replacements)

        # Clear local declaration
        tmpl.set_declaration("")

        system.declaration.update_text()

    @staticmethod
    def replace_call_by_reference_parameters(system, tmpl):
        all_instance_data = get_instance_data_from_system_declaration(system=system)
        # print(all_instance_data)
        tmpl_instance_data = [inst for inst in all_instance_data.values() if inst["templateName"] == tmpl.name]
        assert len(tmpl_instance_data) == 1, f'Exactly one single instances must exist for template "{tmpl.name}".'

        args = tmpl_instance_data[0]["args"]
        var_replacements = []
        shift = 0
        for idx, (param, arg) in enumerate(list(zip(tmpl.parameters, args))):
            if not param.ast["isRef"]:
                continue
            param_name = param.ast["varData"]["varName"]
            var_replacements.append((param_name, arg))
            del tmpl.parameters[idx - shift]
            del args[idx - shift]
            shift += 1

        def model_var_adapt_func(var_replacements_):
            """Helper function for name adaption."""

            def ast_func(ast, _acc):
                """Helper function for name adaption."""
                for arg_name, rep_val_ast in var_replacements_:
                    if ast["astType"] == 'Variable' and ast["name"] == arg_name:
                        ast = copy.deepcopy(rep_val_ast)
                        # if isinstance(rep_val, str):
                        #     ast = {"astType": 'Variable', "name": rep_val}
                        # elif isinstance(rep_val, int):
                        #     ast = {"astType": 'Integer', "val": rep_val}
                        # elif isinstance(rep_val, bool):
                        #     ast = {"astType": 'Boolean', "val": rep_val}
                        break
                return ast

            return ast_func

        adaptions = [model_var_adapt_func(var_replacements_=var_replacements)]

        TemplateModifier.adapt_asts(tmpl=tmpl, adaptions=adaptions)

        system.system_declaration.update_text()

    @staticmethod
    def move_call_by_value_parameters_to_local_declaration(system, tmpl):
        all_instance_data = get_instance_data_from_system_declaration(system=system)
        # print(all_instance_data)
        tmpl_instance_data = [inst for inst in all_instance_data.values() if inst["templateName"] == tmpl.name]
        assert len(tmpl_instance_data) == 1, f'Exactly one single instances must exist for template "{tmpl.name}".'

        args = tmpl_instance_data[0]["args"]
        uppaal_c_parser = UppaalCLanguageParser(semantics=UppaalCLanguageSemantics())
        printer = UppaalCPrinter()
        shift = 0
        local_decl_ext_str = ""
        for idx, (param, arg) in enumerate(list(zip(tmpl.parameters, args))):
            if param.ast["isRef"]:
                continue
            value_str = printer.ast_to_string(arg)
            local_decl_ext_str += f'{param.text} = {value_str};\n'
            del tmpl.parameters[idx - shift]
            del args[idx - shift]
            shift += 1

        # Append new variable declarations to local declaration section
        local_decl_ext_ast = uppaal_c_parser.parse(local_decl_ext_str, rule_name="UppaalDeclaration")
        tmpl.declaration.ast["decls"].extend(local_decl_ext_ast["decls"])
        tmpl.declaration.update_text()

        system.system_declaration.update_text()


def get_instance_data_from_system_declaration(system):
    system_decl_stmts = system.system_declaration.ast["decls"]
    instance_data = {}
    for system_stmt in system_decl_stmts:
        if system_stmt["astType"] == 'Instantiation':
            inst_name = system_stmt["instanceName"]
            instance_data[inst_name] = system_stmt
    return instance_data
