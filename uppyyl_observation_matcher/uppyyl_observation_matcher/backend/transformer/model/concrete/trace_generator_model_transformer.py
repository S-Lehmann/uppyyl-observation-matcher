"""The trace generator model transformer."""

from uppaal_c_language.backend.modifiers.ast_modifier import apply_func_to_ast
from uppaal_c_language.backend.parsers.generated.uppaal_c_language_parser import UppaalCLanguageParser
from uppaal_c_language.backend.parsers.uppaal_c_language_semantics import UppaalCLanguageSemantics
from uppaal_c_language.backend.printers.uppaal_c_language_printer import UppaalCPrinter
from uppaal_model.backend.models.ta.modifiers.ta_modifier import TemplateModifier
from uppyyl_observation_matcher.backend.transformer.model.base_model_transformer import ModelTransformer


class TraceGeneratorModelTransformer(ModelTransformer):
    """A model transformer for trace generation."""

    def __init__(self):
        """Initializes TraceGeneratorModelTransformer."""
        super().__init__()

        self.step_count = None
        self.uppaal_c_parser = UppaalCLanguageParser(semantics=UppaalCLanguageSemantics())

    def prepare(self, model):
        """Performs preparing transformation steps to the input model.

        Args:
            model: The input model for the transformation.

        Returns:
            The transformed model.
        """
        pass

    def finalize(self, model):
        """Performs finalizing transformation steps to the input model.

        Args:
            model: The input model for the transformation.

        Returns:
            The transformed model.
        """
        assert self.step_count is not None
        for tmpl_id, tmpl in model.templates.items():
            TemplateModifier.scale_view(tmpl=tmpl, scale_factor_x=3, scale_factor_y=2)
        self.add_step_counter_and_helper_clocks_to_model(model=model)
        self.add_helper_location_for_intermediate_dbms(model=model)
        self.adapt_queries(model=model)
        self.add_explicit_component_indices(model=model)

    def set_step_count(self, step_count):
        """Sets the number of transition steps to perform during trace generation."""
        self.step_count = step_count

    ####################################################################################################################

    def add_step_counter_and_helper_clocks_to_model(self, model):
        """Adds the step counter and helper clocks (TR is the global reset clock, TG is the global glock) to the model.

        Args:
            model: The source model.
        """
        for tmpl_id, tmpl in model.templates.items():
            for edge_id, edge in tmpl.edges.items():
                if (not edge.sync) or edge.sync.ast["op"] == "!":
                    edge.new_update("_SC++")
                    edge.new_reset("_TR = 0")

        global_decl_ext_str = ""
        global_decl_ext_str += f'clock _TG;\n'
        global_decl_ext_str += f'clock _TR;\n'
        global_decl_ext_str += f'int _SC = 0;\n'
        global_decl_ext_str += f'broadcast chan step;\n'

        global_decl_ext_ast = self.uppaal_c_parser.parse(global_decl_ext_str, rule_name="UppaalDeclaration")
        model.declaration.ast["decls"] = \
            global_decl_ext_ast["decls"] + model.declaration.ast["decls"]
        model.declaration.update_text()

    def add_helper_location_for_intermediate_dbms(self, model):
        """Splits each edge into a first edge applying selects and guards (leading to the DBM with delayed lower
           bound) and a second edge applying the updates and resets (leading to the overall resulting DBM).
           Introduces variables for temporary "select" statement values, as these variables may be used both on the
           first edge (e.g., for channel array access or guards) and on the second edge (e.g., for updates).

        Args:
            model: The source model.
        """
        printer = UppaalCPrinter()

        for tmpl_id, tmpl in model.templates.items():
            id_counter = 0
            local_decl_ext_str = ""
            for edge_idx, (edge_id, edge) in enumerate(tmpl.edges.copy().items()):
                # Determine a suitable position for the intermediate location
                if edge.view["nails"]:
                    last_nail_id = list(edge.view["nails"].keys())[-1]
                    inter_loc_pos = edge.view["nails"][last_nail_id]["pos"]
                    del edge.view["nails"][last_nail_id]
                else:
                    source_loc_pos = edge.source.view["self"]["pos"]
                    target_loc_pos = edge.target.view["self"]["pos"]
                    inter_loc_pos = {
                        "x": int(source_loc_pos["x"] + 0.65 * (target_loc_pos["x"] - source_loc_pos["x"])),
                        "y": int(source_loc_pos["y"] + 0.65 * (target_loc_pos["y"] - source_loc_pos["y"]))
                    }

                # Add the intermediate location and adapt the corresponding edges
                inter_loc = tmpl.new_location(name=f'__h_{id_counter}')
                inter_loc.committed = True
                inter_loc.view["self"]["pos"] = inter_loc_pos

                new_edge = tmpl.new_edge(inter_loc, edge.target)
                new_edge.updates = edge.updates
                new_edge.resets = edge.resets
                edge.updates = []
                edge.resets = []

                edge.target = inter_loc

                id_counter += 1

                if edge.sync:
                    new_edge.set_sync(f'step{edge.sync.ast["op"]}')

                # Introduce explicit variables to store "select" values
                for select in edge.selects:
                    select_var_name = select.ast["name"]
                    select_var_type_ast = select.ast["type"]
                    temp_var_name = f'{select_var_name}_{edge_idx}'
                    temp_var_type_ast = select_var_type_ast
                    local_decl_ext_str += f'{printer.ast_to_string(temp_var_type_ast)} {temp_var_name};\n'
                    edge.new_update(f'{temp_var_name} = {select_var_name}')

                    def edge_var_adapt_func(ast, _acc):
                        """Helper function for variable name adaption."""
                        if ast["astType"] == 'VariableID' and ast["varName"] == select_var_name:
                            ast["varName"] = temp_var_name
                        elif ast["astType"] == 'Variable' and ast["name"] == select_var_name:
                            ast["name"] = temp_var_name
                        return ast

                    for reset in new_edge.resets:
                        reset.ast, _ = apply_func_to_ast(ast=reset.ast, func=edge_var_adapt_func)
                        reset.update_text()

                    for update in new_edge.updates:
                        update.ast, _ = apply_func_to_ast(ast=update.ast, func=edge_var_adapt_func)
                        update.update_text()

            local_decl_ext_ast = self.uppaal_c_parser.parse(text=local_decl_ext_str, rule_name="UppaalDeclaration")
            tmpl.declaration.ast["decls"].extend(local_decl_ext_ast["decls"])
            tmpl.declaration.update_text()

    def adapt_queries(self, model):
        """Removes all original queries and adds the trace matcher query."""
        model.queries = []
        model.new_query(query_text=f'E<> _SC == {self.step_count}', query_comment="The trace generator query.")

    def add_explicit_component_indices(self, model):
        """Adds explicit component indices the locations and edges of the model, so that they can be identified in the
           traces generated by verifyta.

        Args:
            model: The source model.
        """
        decl_ext_ast = self.uppaal_c_parser.parse(f'int __e = -1;', rule_name="UppaalDeclaration")
        for tmpl_id, tmpl in model.templates.items():
            for idx, (location_id, location) in enumerate(tmpl.locations.items()):
                location.name = f'{location.name}__{idx}'

            tmpl.declaration.ast["decls"].extend(decl_ext_ast["decls"])
            tmpl.declaration.update_text()
            for idx, (edge_id, edge) in enumerate(tmpl.edges.items()):
                edge.new_update(f'__e = {idx}')
