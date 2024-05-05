"""The transition simulator model transformer."""

from uppaal_c_language.backend.parsers.generated.uppaal_c_language_parser import UppaalCLanguageParser
from uppaal_c_language.backend.parsers.uppaal_c_language_semantics import UppaalCLanguageSemantics
from uppyyl_observation_matcher.backend.transformer.model.base_model_transformer import ModelTransformer


class TransitionSimulatorModelTransformer(ModelTransformer):
    """A model transformer for transition simulation."""

    def __init__(self):
        """Initializes TransitionSimulatorModelTransformer."""
        super().__init__()

        self.uppaal_c_parser = UppaalCLanguageParser(semantics=UppaalCLanguageSemantics())
        self.edge_trace = None
        self.instance_data = None

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
        self.add_instance_ids(model=model)
        self.add_edge_conditions(model=model)
        self.add_initial_helper_location(model=model)
        self.add_transition_array(model=model)
        self.adapt_queries(model=model)
        self.add_explicit_component_indices(model=model)

    def set_edge_trace(self, edge_trace):
        """Sets the edge trace.

        Args:
            edge_trace: The edge trace.
        """
        self.edge_trace = edge_trace

    def set_instance_data(self, instance_data):
        """Sets the instance data.

        Returns:
            None
        """
        self.instance_data = instance_data

    ####################################################################################################################

    def add_instance_ids(self, model):
        """Adds explicit instance IDs for the processes of the model.

        Args:
            model: The source model.
        """
        global_decl_ext_str = ""
        instance_name_ids = []
        id_counter = 0

        # Extract template names and associate ids to them
        for tmpl_id, tmpl in model.templates.items():
            short_tmpl_name = tmpl.name.replace("_Tmpl", "")
            instance_name_ids.append((f'{short_tmpl_name}_ID', id_counter))
            id_counter += 1

        # Add the instance count and constant identifiers for locations of the template
        global_decl_ext_str += f'const int INST_COUNT = {len(model.templates)};\n'
        global_decl_ext_str += "const int " + ", ".join(map(lambda v: f'{v[0]} = {v[1]}', instance_name_ids)) + ";\n"

        global_decl_ext_ast = self.uppaal_c_parser.parse(global_decl_ext_str, rule_name="UppaalDeclaration")
        model.declaration.ast["decls"].extend(global_decl_ext_ast["decls"])
        model.declaration.update_text()

    @staticmethod
    def add_edge_conditions(model):
        """Adds conditions to the edges (i.e., only take an edge if it should be activated based on the trace data,
           and initialization was finished).

        Args:
            model: The source model.
        """
        for tmpl_id, tmpl in model.templates.items():
            proc_name = tmpl.name.split("_Tmpl")[0]
            for edge_idx, (edge_id, edge) in enumerate(tmpl.edges.items()):
                edge.new_variable_guard(f'TR[TR_idx][{proc_name}_ID] == {edge_idx}')
                edge.new_variable_guard(f'initialized')
                if (not edge.sync) or edge.sync.ast["op"] == "!":
                    edge.new_update("TR_idx++")

    @staticmethod
    def add_initial_helper_location(model):
        """Adds an initial helper location to one of the templates, which is required so that the Uppaal-generated
           trace contains information about the initial system state.

        Args:
            model: The source model.
        """
        first_tmpl = list(model.templates.values())[0]
        orig_init_loc = first_tmpl.init_loc
        orig_init_loc_pos = orig_init_loc.view["self"]["pos"]

        helper_loc = first_tmpl.new_location(name="__h")
        helper_loc.set_committed()
        helper_loc.set_whole_position(pos={"x": orig_init_loc_pos["x"]-50, "y": orig_init_loc_pos["y"]})

        helper_edge = first_tmpl.new_edge(helper_loc, orig_init_loc)
        helper_edge.new_update("initialized = true")

        first_tmpl.set_init_location(helper_loc)

    def add_transition_array(self, model):
        """Adds the transition array to the model, containing the information on which edges to take in which order.

        Args:
            model: The source model.
        """
        edges_idx_trace_list = []
        for edges in self.edge_trace:
            edges_idx_list = []
            for proc_id in self.instance_data.keys():
                if proc_id in edges:
                    edge = edges[proc_id]
                    tmpl = model.get_template_by_name(f'{proc_id}_Tmpl')
                    edge_idx = list(tmpl.edges.keys()).index(edge.id)
                else:
                    edge_idx = -1
                edges_idx_list.append(edge_idx)
            edges_idx_trace_list.append(edges_idx_list)
        edges_idx_trace_list.append([-1] * len(self.instance_data))

        global_decl_ext_str = ""
        global_decl_ext_str += f'const int TR_COUNT = {len(self.edge_trace) + 1};\n'
        global_decl_ext_str += f'int TR_idx = 0;\n'
        global_decl_ext_str += f'bool initialized = false;\n'

        edges_idx_list_strs = []
        for edges_idx_list in edges_idx_trace_list:
            edges_idx_list_str = f'{{{",".join(map(str, edges_idx_list))}}}'
            edges_idx_list_strs.append(edges_idx_list_str)

        global_decl_ext_str += f'const int TR[TR_COUNT][{len(self.instance_data)}] = {{'
        global_decl_ext_str += ",".join(edges_idx_list_strs)
        global_decl_ext_str += f'}};\n'

        global_decl_ext_ast = self.uppaal_c_parser.parse(global_decl_ext_str, rule_name="UppaalDeclaration")
        model.declaration.ast["decls"].extend(global_decl_ext_ast["decls"])
        model.declaration.update_text()

    def adapt_queries(self, model):
        """Removes all original queries and adds the trace matcher query."""
        model.queries = []
        model.new_query(query_text=f'E<> initialized and (TR_idx == {len(self.edge_trace)})',
                        query_comment="The transition query.")

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
