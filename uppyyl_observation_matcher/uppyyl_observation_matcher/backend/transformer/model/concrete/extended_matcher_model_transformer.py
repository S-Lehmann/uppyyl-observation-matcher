"""The extended matcher model transformer."""

import re

from uppaal_c_language.backend.parsers.generated.uppaal_c_language_parser import UppaalCLanguageParser
from uppaal_c_language.backend.parsers.uppaal_c_language_semantics import UppaalCLanguageSemantics
from uppaal_model.backend.models.ta.modifiers.ta_modifier import TemplateModifier
from uppyyl_observation_matcher.backend.helper import load_model_from_file, print_atomic_val
from uppyyl_observation_matcher.backend.transformer.model.base_model_transformer import ModelTransformer
from uppyyl_observation_matcher.definitions import RES_DIR


class ExtendedMatcherModelTransformer(ModelTransformer):
    """A model transformer for extended observation matching."""

    def __init__(self, config):
        """Initializes ExtendedMatcherModelTransformer."""
        super().__init__()

        self.config = config
        self.loaded_matcher_tmpl = None
        self.instance_data = None
        self.observation_data = None
        self.uppaal_c_parser = UppaalCLanguageParser(semantics=UppaalCLanguageSemantics())

    def prepare(self, model):
        """Performs preparing transformation steps to the input model.

        Args:
            model: The input model for the transformation.

        Returns:
            The transformed model.
        """
        self.prepare_base_model(model=model)

    def finalize(self, model):
        """Performs finalizing transformation steps to the input model.

        Args:
            model: The input model for the transformation.

        Returns:
            The transformed model.
        """
        self.insert_observation_matching(model=model)
        self.add_explicit_component_indices(model=model)  # Information to associate trace xml data with model xml data

    def set_observation_data(self, observation_data):
        """Sets the observation data.

        Returns:
            None
        """
        self.observation_data = observation_data

    def set_instance_data(self, instance_data):
        """Sets the instance data.

        Returns:
            None
        """
        self.instance_data = instance_data

    ####################################################################################################################

    def prepare_base_model(self, model):
        """Prepares the base model as follows:
           1. Scale the model visually to make the labels more readable.
           2. Add explicit instance IDs if (committed) location matching is enabled.
           3. Add (committed) location tracking if location matching is enabled.
           4. Add explicit synchronization between the matcher and the original model if committed location tracking
              is enabled.
           5. Adapt the query to check the new reachability property.
           6. Preload the selected matcher model template.

        Args:
            model: The source model which should be prepared.
        """
        if self.config["support_location_matching"] or self.config["support_committed_matching"]:
            for tmpl_id, tmpl in model.templates.items():
                TemplateModifier.scale_view(tmpl=tmpl, scale_factor_x=3, scale_factor_y=2)
            self.add_instance_ids(model=model)

        if self.config["support_location_matching"]:
            self.add_active_location_tracking(model=model)

        if self.config["support_committed_matching"]:
            self.add_committed_location_tracking(model=model)
            self.add_sync_between_matcher_and_original_model(model=model)

        self.adapt_queries(model=model)

        matcher_tmpl = self.select_and_load_matcher_template()
        model.templates["Trace_Matcher_Tmpl"] = matcher_tmpl

    def insert_observation_matching(self, model):
        """Inserts observation matching functionality into the model.

        Args:
            model: The source model.
        """
        self.add_observation_data(model=model)
        self.adapt_matcher_template(model=model)

    def select_and_load_matcher_template(self):
        """Selects and loads a matcher template which fits the enabled matching features. The following 4 matcher
           templates exist:
           1. The normal matcher.
           2. The matcher for delayed observations.
           3. The matcher for committed locations.
           4. The matcher for committed locations and delayed observations.

        Returns:
            The loaded matcher template.
        """
        if self.config["support_committed_matching"]:
            if self.config["support_shifted_matching"]:
                matcher_name = "matcher-committed-and-delayed.xml"
            else:
                matcher_name = "matcher-committed.xml"
        else:
            if self.config["support_shifted_matching"]:
                matcher_name = "matcher-delayed.xml"
            else:
                matcher_name = "matcher-normal.xml"

        matcher_template_system_path = RES_DIR.joinpath("templates", matcher_name)
        matcher_template_system = load_model_from_file(model_path=matcher_template_system_path)
        matcher_tmpl = matcher_template_system.get_template_by_name("Trace_Matcher_Tmpl").copy()
        return matcher_tmpl

    def add_observation_data(self, model):
        """Adds the concrete observation data to the model.

        Args:
            model: The source model.
        """
        global_decl_ext_str = ""
        if self.config["support_partial_matching"]:
            global_decl_ext_str += f'const int NOB = 0;'
        global_decl_ext_str += f'const int OBS_COUNT = {len(self.observation_data)};\n'

        # Define time data array
        time_vals = list(map(lambda obs: obs["t"], self.observation_data))
        time_strs = list(map(lambda v: print_atomic_val(v), time_vals))
        time_var_name = "time"
        global_decl_ext_str += f'const int OBS_{time_var_name}[OBS_COUNT] = {{{",".join(time_strs)}}};\n'

        # Define variable data arrays
        for var_name in self.observation_data[0]["vars"]:
            obs_vals = list(map(lambda obs: obs["vars"][var_name], self.observation_data))
            obs_strs = list(map(lambda v: print_atomic_val(v), obs_vals))
            obs_var_name = re.sub(r'\[(\d+)\]', r'_\1', var_name)
            global_decl_ext_str += f'const int OBS_{obs_var_name}[OBS_COUNT] = {{{",".join(obs_strs)}}};\n'
            if self.config["support_partial_matching"]:
                has_obs_vals = list(map(lambda v: "false" if v in [None, "NOB"] else "true", obs_strs))
                global_decl_ext_str += f'const int HAS_OBS_{obs_var_name}[OBS_COUNT] = {{{",".join(has_obs_vals)}}};\n'

        # Define location data arrays
        for proc_name in self.observation_data[0]["locs"]:
            obs_vals = list(map(lambda obs: obs["locs"][proc_name]["name"], self.observation_data))
            obs_strs = list(map(lambda v: "NOB" if v in [None, "NOB"] else f'{proc_name}_{v}', obs_vals))
            obs_var_name = re.sub(r'\[(\d+)\]', r'_\1', proc_name)
            global_decl_ext_str += f'const int OBS_{obs_var_name}[OBS_COUNT] = {{{",".join(obs_strs)}}};\n'
            if self.config["support_partial_matching"]:
                has_obs_vals = list(map(lambda v: "false" if v in [None, "NOB"] else "true", obs_strs))
                global_decl_ext_str += f'const int HAS_OBS_{obs_var_name}[OBS_COUNT] = {{{",".join(has_obs_vals)}}};\n'

        global_decl_ext_ast = self.uppaal_c_parser.parse(text=global_decl_ext_str, rule_name="UppaalDeclaration")
        model.declaration.ast["decls"].extend(global_decl_ext_ast["decls"])
        model.declaration.update_text()

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

    def add_active_location_tracking(self, model):
        """Adds active location tracking to the model.

        Args:
            model: The source model.
        """
        global_decl_ext_str = ""

        # Add identifier for unnamed active location
        global_decl_ext_str += "const int UNNAMED_LOC = -1;\n"

        # Extract location names and associate ids to locations for each template
        initial_loc_names = []
        for tmpl_id, tmpl in model.templates.items():
            short_tmpl_name = tmpl.name.replace("_Tmpl", "")
            loc_name_ids = []
            id_counter = 0
            for loc_id, loc in tmpl.locations.items():
                if not loc.name:
                    continue
                loc_name_id = id_counter
                loc_name_ids.append((f'{short_tmpl_name}_{loc.name}', f'{loc_name_id}'))
                for in_edge_id, in_edge in loc.in_edges.items():
                    if in_edge.source != in_edge.target:
                        in_edge.new_update(f'LOC[{short_tmpl_name}_ID] = {short_tmpl_name}_{loc.name}')
                id_counter += 1

            # Add constant identifiers for locations of the template, if any named locations exist
            if loc_name_ids:
                global_decl_ext_str += "const int " + ", ".join(map(lambda v: f'{v[0]} = {v[1]}', loc_name_ids)) + ";\n"

            # Get the name of the initial location
            initial_loc_names.append(f'{short_tmpl_name}_{tmpl.init_loc.name}' if tmpl.init_loc.name else "UNNAMED_LOC")

        # Add variable holding the identifier of the currently active location of each instance
        global_decl_ext_str += f'int LOC[INST_COUNT] = {{{",".join(initial_loc_names)}}};\n'

        global_decl_ext_ast = self.uppaal_c_parser.parse(global_decl_ext_str, rule_name="UppaalDeclaration")
        model.declaration.ast["decls"].extend(global_decl_ext_ast["decls"])
        model.declaration.update_text()

    def add_committed_location_tracking(self, model):
        """Adds committed location tracking to the model.

        Args:
            model: The source model.
        """
        global_decl_ext_str = ""

        initial_committed_states = []
        for tmpl_id, tmpl in model.templates.items():
            short_tmpl_name = tmpl.name.replace("_Tmpl", "")
            id_counter = 0
            for loc_id, loc in tmpl.locations.items():
                is_committed_str = "true" if loc.committed else "false"
                for in_edge_id, in_edge in loc.in_edges.items():
                    if in_edge.source != in_edge.target:
                        in_edge.new_update(f'COMM[{short_tmpl_name}_ID] = {is_committed_str}')
                id_counter += 1

            initial_committed_states.append((f'{short_tmpl_name}', tmpl.init_loc.committed))

        # Add variable holding the "committed" state of all instances
        initial_loc_is_committed_strs = ["true" if c[1] else "false" for c in initial_committed_states]
        global_decl_ext_str += f'int COMM[INST_COUNT] = {{{",".join(initial_loc_is_committed_strs)}}};\n'

        global_decl_ext_ast = self.uppaal_c_parser.parse(global_decl_ext_str, rule_name="UppaalDeclaration")
        model.declaration.ast["decls"].extend(global_decl_ext_ast["decls"])
        model.declaration.update_text()

    @staticmethod
    def add_sync_between_matcher_and_original_model(model):
        """Adds explicit synchronization between the matcher model and the original model.

        Args:
            model: The source model.
        """
        for tmpl_id, tmpl in model.templates.items():
            id_counter = 0
            for edge_id, edge in tmpl.edges.copy().items():
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
                inter_loc.urgent = True
                inter_loc.view["self"]["pos"] = inter_loc_pos

                sync_edge = tmpl.new_edge(inter_loc, edge.target)
                sync_edge.set_sync("_step?")
                for inv in edge.target.invariants:
                    sync_edge.new_clock_guard(inv.text)

                edge.target = inter_loc

                id_counter += 1

                edge.new_update("_stepped=true")

                edge.new_variable_guard("!_stepped")

    @staticmethod
    def adapt_queries(model):
        """Removes all original queries and adds the trace matcher query."""
        model.queries = []
        model.new_query(query_text=f'E<> Trace_Matcher.S', query_comment="The trace matcher query.")

    def adapt_matcher_template(self, model):
        """Adds an instance of the preloaded matcher template to the system, and adapts the matcher template based
           on the enabled matching features.

        Args:
            model: The source model.
        """
        matcher_tmpl = model.get_template_by_name("Trace_Matcher_Tmpl")

        # Add the matcher instance to the system declaration
        matcher_inst_name = f'Trace_Matcher'
        matcher_tmpl_name = f'Trace_Matcher_Tmpl'
        matcher_instance_ast = {
            "astType": 'Instantiation',
            "instanceName": matcher_inst_name,
            "params": [],
            "templateName": matcher_tmpl_name,
            "args": []
        }
        model.system_declaration.ast["decls"].append(matcher_instance_ast)
        model.system_declaration.ast["systemDecl"]["processNames"][0].append(matcher_inst_name)

        # Add synchronization variables to global declaration
        global_decl_ext_str = ""

        if self.config["support_shifted_matching"]:
            maximum_initial_delay = self.config["maximum_initial_delay"]
            global_decl_ext_str += f'const int DELAY = {maximum_initial_delay};'

        if self.config["support_committed_matching"]:
            global_decl_ext_str += f'broadcast chan _step;'
            global_decl_ext_str += f'bool _stepped = true;'
            global_decl_ext_str += f'bool is_committed() {{return exists (i : int[0, INST_COUNT - 1]) COMM[i];}}'

        global_decl_ext_ast = self.uppaal_c_parser.parse(global_decl_ext_str, rule_name="UppaalDeclaration")
        model.declaration.ast["decls"].extend(global_decl_ext_ast["decls"])

        # Replace the "check_time()" function with actual time constraints
        t_obs_deviation = self.config["allowed_deviations"].get("t", None)

        if self.config["support_committed_matching"]:
            check_time_locs = ["m_i", "m_ic"]
            check_time_edges = [("m_i", "h"), ("m_ic", "h_c")]
        else:
            check_time_locs = ["m_i"]
            check_time_edges = [("m_i", "h")]

        for loc_name, edge_name in zip(check_time_locs, check_time_edges):
            loc_m_i = matcher_tmpl.get_location_by_name(loc_name)
            for invariant in loc_m_i.invariants.copy():
                if invariant.text == "check_time()":
                    loc_m_i.invariants.remove(invariant)
            if t_obs_deviation:
                loc_m_i.new_invariant(f'tt <= OBS_time[i] + DEV_time')
            else:
                loc_m_i.new_invariant(f'tt <= OBS_time[i]')

            edge_m_i_h = list(filter(lambda e: e.target.name == edge_name[1], loc_m_i.out_edges.values()))[0]
            for variable_guard in edge_m_i_h.variable_guards.copy():
                if variable_guard.text == "check_time()":
                    edge_m_i_h.variable_guards.remove(variable_guard)
            if t_obs_deviation:
                edge_m_i_h.new_clock_guard(f'tt >= OBS_time[i] - DEV_time')
            else:
                edge_m_i_h.new_clock_guard(f'tt >= OBS_time[i]')

        # Fill body of "check_vars()" function
        # Variables
        var_strs = []
        for var_name in self.observation_data[0]["vars"]:
            obs_var_name = re.sub(r'\[(\d+)\]', r'_\1', var_name)
            var_str = ""
            var_deviation = self.config["allowed_deviations"].get(var_name, None)
            if var_deviation:
                var_str += f'({var_name} >= OBS_{obs_var_name}[i] - DEV_{obs_var_name}) && ' \
                           f'({var_name} <= OBS_{obs_var_name}[i] + DEV_{obs_var_name})'
            else:
                var_str += f'{var_name} == OBS_{obs_var_name}[i]'
            if self.config["support_partial_matching"]:
                var_str = f'(!HAS_OBS_{obs_var_name}[i] || ({var_str}))'
            var_strs.append(var_str)

        # Locations
        for var_name in self.observation_data[0]["locs"]:
            obs_var_name = re.sub(r'\[(\d+)\]', r'_\1', var_name)
            var_str = ""
            var_str += f'LOC[{obs_var_name}_ID] == OBS_{obs_var_name}[i]'
            if self.config["support_partial_matching"]:
                var_str = f'(!HAS_OBS_{obs_var_name}[i] || ({var_str}))'
            var_strs.append(var_str)

        check_vars_str = " && ".join(var_strs)
        check_vars_func_str = f'bool check_vars() {{return {check_vars_str};}}\n'

        # Compose new local declaration for the trace matcher template
        matcher_tmpl_decl_str = ""
        matcher_tmpl_decl_str += "clock tt;\n"
        matcher_tmpl_decl_str += "int i=0;\n"
        matcher_tmpl_decl_str += check_vars_func_str
        matcher_tmpl_decl_ast = self.uppaal_c_parser.parse(matcher_tmpl_decl_str, rule_name="UppaalDeclaration")
        matcher_tmpl.declaration.ast["decls"] = matcher_tmpl_decl_ast["decls"]
        matcher_tmpl.declaration.update_text()

        # Add deviation variables to the global declaration
        global_decl_ext_str = ""
        for var_name, deviation in self.config["allowed_deviations"].items():
            if deviation > 0:
                var_name = "time" if var_name == "t" else var_name
                global_decl_ext_str += f'const int DEV_{var_name} = {deviation};\n'
        global_decl_ext_ast = self.uppaal_c_parser.parse(global_decl_ext_str, rule_name="UppaalDeclaration")
        model.declaration.ast["decls"].extend(global_decl_ext_ast["decls"])

        model.declaration.update_text()
        model.system_declaration.update_text()

    def add_explicit_component_indices(self, model):
        """Adds explicit component indices the locations and edges of the model, so that they can be identified in the
           traces generated by verifyta.

        Args:
            model: The source model.
        """
        final_matcher_location = model.get_template_by_name("Trace_Matcher_Tmpl").get_location_by_name("S")
        decl_ext_ast = self.uppaal_c_parser.parse(f'int __e = -1;', rule_name="UppaalDeclaration")
        for tmpl_id, tmpl in model.templates.items():
            for idx, (location_id, location) in enumerate(tmpl.locations.items()):
                location.name = f'{location.name}__{idx}'

            tmpl.declaration.ast["decls"].extend(decl_ext_ast["decls"])
            tmpl.declaration.update_text()
            for idx, (edge_id, edge) in enumerate(tmpl.edges.items()):
                edge.new_update(f'__e = {idx}')

        model.queries = []
        model.new_query(query_text=f'E<> Trace_Matcher.{final_matcher_location.name}',
                        query_comment="The trace matcher query.")
