"""The transition simulator model trace transformer."""

from uppyyl_observation_matcher.backend.transformer.state.concrete.transition_simulator_model_state_transformer import \
    TransitionSimulatorModelStateTransformer
from uppyyl_observation_matcher.backend.transformer.trace.base_trace_transformer import TraceTransformer


class TransitionSimulatorModelTraceTransformer(TraceTransformer):
    def __init__(self, source_system, target_system):
        super().__init__(source_system=source_system, target_system=target_system)

    def init_state_transformer(self):
        self.state_transformer = TransitionSimulatorModelStateTransformer(
            source_system=self.source_system, target_system=self.target_system)

    def transform_trace(self, trace):
        trace.init_state = trace.transitions[0].target_state
        del trace.transitions[0]
