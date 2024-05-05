"""The abstract trace transformer."""

import abc


class TraceTransformer(abc.ABC):
    """An abstract trace transformer."""

    def __init__(self, source_system, target_system):
        """Initializes TraceTransformer.

        Args:
            source_system: The source system which the trace originates from.
            target_system: The target system which the trace should be transformed to.
        """
        self.source_system = source_system
        self.target_system = target_system
        self.state_transformer = None
        self.init_state_transformer()

    @abc.abstractmethod
    def init_state_transformer(self):
        """Initialized the state transformer."""
        pass

    def transform(self, trace):
        """Applies the transformation ta a given trace.

        Args:
            trace: The given trace.
        """
        self.transform_trace(trace=trace)
        self.transform_states(trace=trace)
        if self.source_system != self.target_system:
            self.translate_edges_to_target_system(trace=trace)

    def transform_states(self, trace):
        """Applies transformations to the states of a given trace.

        Args:
            trace: The given trace.
        """
        if not self.state_transformer:
            return
        for state in trace.get_states():
            self.state_transformer.transform(state=state)

    def transform_trace(self, trace):
        """Applies transformations to the trace as a whole.

        Args:
            trace: The given trace.
        """
        pass

    def translate_edges_to_target_system(self, trace):
        """Translates the edges of a trace to the edges of a target system. This step is necessary to update
           the edge object references during transformation.

        Args:
            trace: The given trace.
        """
        for tr in trace.transitions:
            target_edges = {}
            for proc_id, edge in tr.triggered_edges.items():
                source_tmpl = self.source_system.get_template_by_name(f'{proc_id}_Tmpl')
                target_tmpl = self.target_system.get_template_by_name(f'{proc_id}_Tmpl')
                try:
                    edge_idx = list(source_tmpl.edges.values()).index(edge)
                except ValueError:
                    print(f'Edge "{edge.source.name} -> {edge.target.name}" (id: "{edge.id}") not in list.')
                    print(f'Existing edges: {source_tmpl.locations.keys()}')
                    raise
                target_edge = list(target_tmpl.edges.values())[edge_idx]
                target_edges[proc_id] = target_edge
            tr.triggered_edges = target_edges
