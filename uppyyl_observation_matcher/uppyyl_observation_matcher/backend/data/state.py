"""A state of the Uppaal system."""


class State:
    """A state of the Uppaal system."""

    def __init__(self, locs, dbm, variables):
        """Initializes State.

        Args:
            locs: The location data of the state.
            dbm: The DBM data of the state.
            variables: The variable data of the state.
        """
        self.locs = locs
        self.dbm = dbm
        self.vars = variables

    def includes(self, state):
        """Checks if another symbolic state is included in this state.

        Args:
            state: The other symbolic state.

        Returns:
            The boolean inclusion result.
        """
        for proc_id in state.locs.keys():
            if self.locs[proc_id] != state.locs[proc_id]:
                print(
                    f'Location of process "{proc_id}" does not match. '
                    f'({self.locs[proc_id].name}, {state.locs[proc_id].name})')
                return False
        if not self.dbm.includes(other=state.dbm):
            print(f'DBM not included:')
            print(self.dbm)
            print(state.dbm)
            return False
        for var in state.vars.keys():
            if self.vars[var] != state.vars[var]:
                print(f'Variable "{var}" does not match. ({self.vars[var]}, {state.vars[var]})')
                return False
        return True

    def copy(self):
        """Copies the state.

        Returns:
            The copied state.
        """
        copy_obj = State(locs=self.locs.copy(), dbm=self.dbm.copy(), variables=self.vars.copy())
        return copy_obj

    def __str__(self):
        string = "("
        string += "C=C"
        string += ", L=(" + ", ".join(map(lambda l: f'{l[0]}.{l[1].name}', self.locs.items())) + ")"
        string += ", V=(" + ", ".join(map(lambda v: f'{v[0]}: {v[1]}', self.vars.items())) + ")"
        string += ")"
        return string
