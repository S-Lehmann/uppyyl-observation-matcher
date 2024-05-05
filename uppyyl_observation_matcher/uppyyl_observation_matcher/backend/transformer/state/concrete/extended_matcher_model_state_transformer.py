"""The extended matcher model state transformer."""

from uppyyl_observation_matcher.backend.transformer.state.base_state_transformer import StateTransformer, \
    remove_variables_from_state, remove_clocks_from_state, remove_locations_from_state


class ExtendedMatcherModelStateTransformer(StateTransformer):
    """The extended matcher model state transformer."""

    def __init__(self, source_system, target_system):
        """Initializes ExtendedMatcherModelStateTransformer.

        Args:
            source_system: The source system which the state originates from.
            target_system: The target system which the state should be transformed to.
        """
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
            return (process == "sys" and var.startswith(("LOC", "COMM", "_stepped"))) or \
                process == "Trace_Matcher" or var == "__e"

        remove_variables_from_state(state=state, matcher_func=matcher_func)

    def transform_clocks(self, state):
        def matcher_func(clock):
            """The matcher function which specifies which clocks to remove from the state.

            Args:
                clock: The clock for which removal is decided.

            Returns:
                A boolean indicator of whether the clock should be removed.
            """
            return clock in ["Trace_Matcher.tt"]

        remove_clocks_from_state(state=state, matcher_func=matcher_func)

    def transform_locations(self, state):
        def matcher_func(process):
            """The matcher function which specifies which locations to remove from the state.

            Args:
                process: The process for which the location removal is decided.

            Returns:
                A boolean indicator of whether the location should be removed.
            """
            return process in ["Trace_Matcher"]

        remove_locations_from_state(state=state, matcher_func=matcher_func)
