"""The trace generator model trace transformer."""

from uppyyl_observation_matcher.backend.data.state import State
from uppyyl_observation_matcher.backend.data.transition import Transition
from uppyyl_observation_matcher.backend.transformer.state.concrete.trace_generator_model_state_transformer import \
    TraceGeneratorModelStateTransformer
from uppyyl_observation_matcher.backend.transformer.trace.base_trace_transformer import TraceTransformer


class TraceGeneratorModelTraceTransformer(TraceTransformer):
    def __init__(self, source_system, target_system):
        super().__init__(source_system=source_system, target_system=target_system)

    def init_state_transformer(self):
        self.state_transformer = TraceGeneratorModelStateTransformer(
            source_system=self.source_system, target_system=self.target_system)

    def transform_trace(self, trace):
        transition_pairs = []
        for i in range(0, len(trace.transitions), 2):
            transition_pair = (trace.transitions[i], trace.transitions[i+1])
            transition_pairs.append(transition_pair)

        transitions = []
        for tr_1, tr_2 in transition_pairs:
            new_tr = Transition(source_state=tr_1.source_state, target_state=tr_2.target_state,
                                triggered_edges=tr_1.triggered_edges)
            new_tr.intermediate_states["delay_state"] = State(
                locs=tr_1.source_state.locs.copy(),
                dbm=tr_1.target_state.dbm.copy(),
                variables=tr_1.source_state.vars.copy()
            )
            transitions.append(new_tr)

        trace.init_state = transitions[0].source_state
        trace.transitions = transitions
