"""The raw matcher model transformer."""

from uppaal_c_language.backend.parsers.generated.uppaal_c_language_parser import UppaalCLanguageParser
from uppaal_c_language.backend.parsers.uppaal_c_language_semantics import UppaalCLanguageSemantics
from uppaal_model.backend.helper import unique_id
from uppaal_model.backend.models.ta.ta import Template
from uppyyl_observation_matcher.backend.transformer.model.base_model_transformer import ModelTransformer


class RawMatcherModelTransformer(ModelTransformer):
    """A model transformer for raw observation matching."""

    def __init__(self, config):
        """Initializes RawMatcherModelTransformer."""
        super().__init__()

        self.config = config
        self.observation_data = None
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
        matcher_tmpl = self.generate_matcher_template()
        self.insert_matcher_template(model=model, matcher_tmpl=matcher_tmpl)
        self.adapt_queries(model=model)
        self.add_explicit_component_indices(model=model)  # Information to associate trace xml data with model xml data

    def set_observation_data(self, observation_data):
        """Sets the observation data.

        Returns:
            None
        """
        self.observation_data = observation_data

    ####################################################################################################################

    def generate_matcher_template(self):
        """Generates the matcher template.

        Returns:
            The generated matcher template.
        """
        matcher_tmpl = Template(name="Trace_Matcher_Tmpl")

        m_0 = matcher_tmpl.new_location(name="m_0")
        m_0.set_whole_position(pos={"x": 0, "y": 0})
        matcher_tmpl.set_init_location(loc=m_0)

        prev_last_loc = m_0
        data_points = self.observation_data
        for i, data_point in enumerate(data_points):
            # Add locations
            m_i_1 = matcher_tmpl.new_location(name=f'm_{i + 1}_1')
            m_i_1.set_whole_position(pos={"x": 200, "y": i * 200})
            m_i_2 = matcher_tmpl.new_location(name=f'm_{i + 1}_2')
            m_i_2.set_whole_position(pos={"x": 400, "y": i * 200})
            m_i_3 = matcher_tmpl.new_location(name=f'm_{i + 1}_3')
            m_i_3.set_whole_position(pos={"x": 600, "y": i * 200})
            m_i_4 = matcher_tmpl.new_location(name=f'm_{i + 1}_4')
            m_i_4.set_whole_position(pos={"x": 800, "y": i * 200})
            m_i_5 = matcher_tmpl.new_location(name=f'm_{i + 1}_5')
            m_i_5.set_whole_position(pos={"x": 1000, "y": i * 200})

            # Add edges
            e_0_1 = matcher_tmpl.new_edge(source=prev_last_loc, target=m_i_1)
            if prev_last_loc == m_0:
                e_0_1.new_clock_guard(grd_data="k==0")
                e_0_1.new_update(updt_data="tt=0")
                e_0_1.new_update(updt_data="k=0")
            else:
                e_0_1.new_clock_guard(grd_data="k==0")
                e_0_1.new_update(updt_data="k=0")

                all_nail_pos = [
                    {"x": prev_last_loc.view["self"]["pos"]["x"], "y": prev_last_loc.view["self"]["pos"]["y"] + 100},
                    {"x": m_i_1.view["self"]["pos"]["x"], "y": prev_last_loc.view["self"]["pos"]["y"] + 100},
                ]
                for nail_pos in all_nail_pos:
                    nail = {"id": unique_id("nail"), "pos": nail_pos}
                    e_0_1.view["nails"][nail["id"]] = nail

            e_1_2 = matcher_tmpl.new_edge(source=m_i_1, target=m_i_2)
            e_1_2.new_update(updt_data="k=0")
            e_2_3 = matcher_tmpl.new_edge(source=m_i_2, target=m_i_3)
            e_2_3.new_clock_guard(grd_data="k==0")
            e_2_3.new_clock_guard(grd_data=f'tt>={data_point["t"]}')
            e_2_3.new_update(updt_data="k=0")
            e_3_4 = matcher_tmpl.new_edge(source=m_i_3, target=m_i_4)
            e_3_4.new_clock_guard(grd_data="k==0")
            e_3_4.new_clock_guard(grd_data=f'tt<={data_point["t"]}')
            e_3_4.new_update(updt_data="k=0")
            e_4_5 = matcher_tmpl.new_edge(source=m_i_4, target=m_i_5)
            e_4_5.new_clock_guard(grd_data="k==0")
            for var, val in data_point["vars"].items():
                e_4_5.new_variable_guard(grd_data=f'{var}>={val}')
                e_4_5.new_variable_guard(grd_data=f'{var}<={val}')

            # Update last location
            prev_last_loc = m_i_5

        m_t = matcher_tmpl.new_location(name="m_T")
        m_t.set_whole_position(pos={"x": 1200, "y": (len(data_points) - 1) * 200})
        e_5_t = matcher_tmpl.new_edge(source=prev_last_loc, target=m_t)
        e_5_t.new_clock_guard(grd_data="k==0")

        # Set declaration
        matcher_tmpl.set_declaration(decl="clock tt, k;")

        return matcher_tmpl

    @staticmethod
    def adapt_queries(model):
        """Removes all original queries and adds the trace matcher query."""
        model.queries = []
        model.new_query(query_text=f'E<> Trace_Matcher.m_T', query_comment="The trace matcher query.")

    @staticmethod
    def insert_matcher_template(model, matcher_tmpl):
        """Inserts the matcher template into the model.

        Args:
            model: The source model.
            matcher_tmpl: The matcher template to insert into the model.
        """
        # Copy matcher template into the adapted system
        model.templates[matcher_tmpl.id] = matcher_tmpl

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

        model.declaration.update_text()
        model.system_declaration.update_text()

    def add_explicit_component_indices(self, model):
        """Adds explicit component indices the locations and edges of the model, so that they can be identified in the
           traces generated by verifyta.

        Args:
            model: The source model.
        """
        final_matcher_location = model.get_template_by_name("Trace_Matcher_Tmpl").get_location_by_name("m_T")
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
