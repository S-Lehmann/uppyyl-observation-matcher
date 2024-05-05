"""The trace generator model state transformer."""

import re

from uppyyl_observation_matcher.backend.transformer.state.base_state_transformer import StateTransformer, \
    remove_variables_from_state


class TraceGeneratorModelStateTransformer(StateTransformer):
    def __init__(self, source_system, target_system):
        super().__init__(source_system=source_system, target_system=target_system)

    def transform_variables(self, state):
        def matcher_func(process, var):
            """The matcher function which specifies which variables to remove from the state.

            Args:
                process: The process for which removal is decided.
                var: The variable of the given process for which removal is decided.

            Returns:
                A boolean indicator of whether the variable should be removed.
            """
            return (process == "sys" and var == "_SC") or var == "__e" or re.match(r'e_\d+', var)
        remove_variables_from_state(state=state, matcher_func=matcher_func)

    def transform_clocks(self, state):
        pass

    def transform_locations(self, state):
        pass
