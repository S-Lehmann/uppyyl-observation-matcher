"""A transition of the Uppaal system."""


class Transition:
    """A transition of the Uppaal system."""

    def __init__(self, source_state, target_state, triggered_edges):
        """Initializes Transition.

        Args:
            source_state: The source state of the transition.
            target_state: The target state of the transition.
            triggered_edges: The edges triggered in the transition.
        """
        self.source_state = source_state
        self.target_state = target_state
        self.intermediate_states = {}
        self.triggered_edges = triggered_edges

    def __str__(self):
        string = f'{self.source_state} -> {self.target_state}'
        return string
