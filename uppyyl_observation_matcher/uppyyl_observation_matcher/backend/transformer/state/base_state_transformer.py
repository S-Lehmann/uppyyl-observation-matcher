"""The abstract state transformer."""

import abc


class StateTransformer(abc.ABC):
    """An abstract state transformer."""
    def __init__(self, source_system, target_system):
        """Initializes StateTransformer.

        Args:
            source_system: The source system which the state originates from.
            target_system: The target system which the state should be transformed to.
        """
        self.source_system = source_system
        self.target_system = target_system

    def transform(self, state):
        """Applies the transformation ta a given state.

        Args:
            state: The given state.
        """
        self.transform_clocks(state=state)
        self.transform_locations(state=state)
        self.transform_variables(state=state)
        if self.source_system != self.target_system:
            self.translate_locations_to_target_system(state=state)

    def translate_locations_to_target_system(self, state):
        """Translates the locations of a state to the locations of a target system. This step is necessary to update
           the location object references during transformation.

        Args:
            state: The given state.
        """
        target_locs = {}
        for proc_id, loc in state.locs.items():
            source_tmpl = self.source_system.get_template_by_name(f'{proc_id}_Tmpl')
            target_tmpl = self.target_system.get_template_by_name(f'{proc_id}_Tmpl')
            try:
                loc_idx = list(source_tmpl.locations.values()).index(loc)
            except ValueError:
                print(f'Location "{loc.name}" (id: "{loc.id}") not in list.')
                print(f'Existing locations: {source_tmpl.locations.keys()}')
                raise
            target_loc = list(target_tmpl.locations.values())[loc_idx]
            target_locs[proc_id] = target_loc
        state.locs = target_locs

    def transform_variables(self, state):
        """Applies transformations to the variables of a given state.

        Args:
            state: The given state.
        """
        pass

    def transform_clocks(self, state):
        """Applies transformations to the clocks of a given state.

        Args:
            state: The given state.
        """
        pass

    def transform_locations(self, state):
        """Applies transformations to the location data of a given state.

        Args:
            state: The given state.
        """
        pass


########################################################################################################################

def remove_variables_from_state(state, matcher_func):
    """Removes variables from a given state selected by a matcher function.

    Args:
        state: The given state.
        matcher_func: The matcher function selecting the variables to remove.
    """
    for key in list(state.vars.keys()):
        proc, v = key.split(".", 1)
        if matcher_func(proc, v):
            del state.vars[key]


def remove_locations_from_state(state, matcher_func):
    """Removes locations from a given state selected by a matcher function.

    Args:
        state: The given state.
        matcher_func: The matcher function selecting the locations to remove.
    """
    for proc in list(state.locs.keys()):
        if matcher_func(proc):
            state.locs.pop(proc, None)


def remove_clocks_from_state(state, matcher_func):
    """Removes clocks from a given state selected by a matcher function.

    Args:
        state: The given state.
        matcher_func: The matcher function selecting the clocks to remove.
    """
    clocks = state.dbm.clocks
    remaining_clocks = []
    for clock in clocks:
        if not matcher_func(clock):
            remaining_clocks.append(clock)

    state.dbm.update_clocks(clocks=remaining_clocks)
