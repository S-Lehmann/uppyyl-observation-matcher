"""The extended matcher model trace transformer."""

from uppyyl_observation_matcher.backend.data.transition import Transition
from uppyyl_observation_matcher.backend.helper import dbm_union
from uppyyl_observation_matcher.backend.transformer.state.concrete.extended_matcher_model_state_transformer import \
    ExtendedMatcherModelStateTransformer
from uppyyl_observation_matcher.backend.transformer.trace.base_trace_transformer import TraceTransformer


class ExtendedMatcherModelTraceTransformer(TraceTransformer):
    def __init__(self, source_system, target_system):
        super().__init__(source_system=source_system, target_system=target_system)

    def init_state_transformer(self):
        self.state_transformer = ExtendedMatcherModelStateTransformer(
            source_system=self.source_system, target_system=self.target_system)

    def transform_trace(self, trace):
        state_groups = []
        current_state_group = []
        edges_between_groups = []

        # Filter out matcher states
        for tr in trace.transitions:
            if tr.source_state.locs["Trace_Matcher"].name.startswith(("d", "m_i", "d_c", "m_ic")) and \
                    not any([loc[1].name.startswith("__h") for loc in tr.source_state.locs.items()]):
                current_state_group.append(tr.source_state)
                if tr.target_state.locs["Trace_Matcher"].name.startswith(("d", "m_i", "d_c", "m_ic")):
                    state_groups.append(current_state_group)
                    current_state_group = []
                    edges_between_groups.append(tr.triggered_edges)
        if current_state_group:
            state_groups.append(current_state_group)
        # print(state_groups)

        # Merge clock states in state groups
        states = []
        for state_group in state_groups:
            combined_state = state_group[0].copy()
            for state in state_group[1:]:
                dbm_union(combined_state.dbm, state.dbm)
            states.append(combined_state)

        # Compose updated transitions list
        transitions = []
        for s_1, s_2, edges in zip(states[:-1], states[1:], edges_between_groups):
            tr = Transition(source_state=s_1, target_state=s_2, triggered_edges=edges)
            transitions.append(tr)

        trace.init_state = states[0]
        trace.transitions = transitions
