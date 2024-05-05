"""A trace of the Uppaal system."""

from uppyyl_observation_matcher.backend.data.transition import Transition


class Trace:
    """A trace of the Uppaal system."""

    def __init__(self, init_state, transitions):
        """Initializes Trace.

        Args:
            init_state: The initial state of the trace.
            transitions: The transitions contained in the trace.
        """
        self.init_state = init_state
        self.transitions = transitions

    def get_states(self, include_intermediate_states=True):
        """Gets the list of states of the trace.

        Args:
            include_intermediate_states: A flag indicating whether intermediate states should be included in the list
                                         of states.

        Returns:
            The list of states.
        """
        states = [self.init_state]
        for transition in self.transitions:
            if include_intermediate_states:
                states.extend(transition.intermediate_states.values())
            states.append(transition.target_state)
        return states

    def includes(self, trace):
        """Checks if another symbolic trace is included in this trace.

        Args:
            trace: The other symbolic trace.

        Returns:
            The boolean inclusion result.
        """
        if not self.init_state.includes(trace.init_state):
            print(f'Initial states do not match:')
            print(f'self: {self.init_state}')
            print(f'other: {trace.init_state}')
            return False
        for tr, tr_other in zip(self.transitions, trace.transitions):
            for proc_id in tr_other.triggered_edges.keys():
                if tr.triggered_edges[proc_id] != tr_other.triggered_edges[proc_id]:
                    print(f'Triggered edges do not match for process "{proc_id}":')
                    print(f'self: {tr.triggered_edges}')
                    print(f'other: {tr_other.triggered_edges}')
                    return False
            if not tr.target_state.includes(tr_other.target_state):
                print(f'Target states do not match:')
                print(f'self: {tr.target_state}')
                print(f'other: {tr_other.target_state}')
                return False
        return True

    def copy(self):
        """Copies the trace.

        Returns:
            The copied trace.
        """
        copy_states = [s.copy() for s in self.get_states()]
        copy_triggered_edges = [tr.triggered_edges.copy() for tr in self.transitions]
        copy_transitions = []
        for source_state, target_state, triggered_edges in zip(copy_states[:-1], copy_states[1:], copy_triggered_edges):
            copy_tr = Transition(source_state=source_state, target_state=target_state, triggered_edges=triggered_edges)
            copy_transitions.append(copy_tr)
        copy_obj = Trace(init_state=copy_states[0], transitions=copy_transitions)
        return copy_obj

    def __str__(self):
        string = ""
        string += str(self.init_state)
        for transition in self.transitions:
            triggered_edges = [f'({e[0]}, {e[1].source.name}, {e[1].target.name})' for e
                               in transition.triggered_edges.items()]
            string += f'\n-- {", ".join(triggered_edges)} -->'
            string += f'\n{transition.target_state}'
        return string
