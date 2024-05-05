"""The observation generator."""

import copy
import random

import numpy as np

from uppyyl_observation_matcher.backend.data.dbm import DBMConstraint
from uppyyl_observation_matcher.backend.helper import save_model_to_file, load_trace_from_file
from uppyyl_observation_matcher.backend.data.trace import Trace
from uppyyl_observation_matcher.backend.data.transition import Transition
from uppyyl_observation_matcher.backend.transformer.model.concrete.trace_generator_model_transformer import \
    TraceGeneratorModelTransformer
from uppyyl_observation_matcher.backend.interface.verifyta import VerifyTAInterface
from uppyyl_observation_matcher.backend.transformer.observation.concrete.generated_observation_transformer import \
    GeneratedObservationTransformer
from uppyyl_observation_matcher.backend.transformer.observation.concrete.negative_observation_transformer import \
    NegativeObservationTransformer
from uppyyl_observation_matcher.backend.transformer.trace.concrete.trace_generator_model_trace_transformer import \
    TraceGeneratorModelTraceTransformer


class ObservationGenerator:
    """The observation generator."""
    def __init__(self, config, model):
        self.config = config
        self.input_model = None
        self.trace_generator_model = None
        self.set_model(model=model)
        self.trace_transformer = None

    def generate(self):
        """Generates a single observation sequence of a model.

        Returns:
            The generated observation.
        """
        if not self.trace_generator_model:
            self.create_trace_generator_model()
        is_success, symbolic_trace = self.generate_trace()
        self.trace_transformer.transform(symbolic_trace)
        process_names = list(symbolic_trace.init_state.locs.keys())

        semi_concrete_trace = extract_deterministic_trace(config=self.config, symbolic_trace=symbolic_trace)
        raw_data_trace = extract_data_points_from_deterministic_trace(deterministic_trace=semi_concrete_trace)

        observation_transformer = GeneratedObservationTransformer(config=self.config, process_names=process_names)
        adapted_data_trace = copy.deepcopy(raw_data_trace)
        observation_transformer.transform(adapted_data_trace)

        observation_data = adapted_data_trace

        return observation_data

    def generate_negative(self):
        """Generates a negative observation (i.e., an observation that is not contained in the model).

        Returns:
            The generated negative observation.
        """
        if not self.trace_generator_model:
            self.create_trace_generator_model()
        is_success, symbolic_trace = self.generate_trace()
        self.trace_transformer.transform(symbolic_trace)

        semi_concrete_trace = extract_deterministic_trace(config=self.config, symbolic_trace=symbolic_trace)
        raw_data_trace = extract_data_points_from_deterministic_trace(deterministic_trace=semi_concrete_trace)

        observation_transformer = NegativeObservationTransformer(
            config=self.config, reference_trace=semi_concrete_trace)
        adapted_data_trace = copy.deepcopy(raw_data_trace)
        observation_transformer.transform(adapted_data_trace)

        observation_data = adapted_data_trace

        return observation_data

    def generate_trace(self):
        """Generates a model trace using verifyta.

        Returns:
            The generated model trace.
        """
        if not self.trace_generator_model:
            raise Exception("Trace generator model needs to be generated before data trace generation.")
        is_success = perform_trace_generation_with_uppaal(config=self.config)

        if is_success:
            random_trace = load_trace_from_file(
                trace_file_path=self.config["random_trace_file_path"], system=self.trace_generator_model)
        else:
            random_trace = None

        return is_success, random_trace

    def create_trace_generator_model(self):
        """Creates the model variant used with verifyta for the generation of traces."""
        trace_generator_model_transformer = TraceGeneratorModelTransformer()
        trace_generator_model_transformer.set_step_count(step_count=self.config["step_count"])
        self.trace_generator_model = self.input_model.copy()
        trace_generator_model_transformer.transform(model=self.trace_generator_model)

        save_model_to_file(model=self.trace_generator_model,
                           model_path=self.config["random_trace_generator_model_file_path"])

        self.trace_transformer = TraceGeneratorModelTraceTransformer(
            source_system=self.trace_generator_model, target_system=self.input_model)

    def set_model(self, model):
        """Sets the model for which observations are generated.

        Args:
            model: The input model.
        """
        self.input_model = model
        self.trace_generator_model = None

    ####################################################################################################################


def perform_trace_generation_with_uppaal(config):
    """Performs the trace generation with Uppaal verifyta.

    Args:
        config: The configration data for verifyta.

    Returns:
        The generated trace.
    """
    verifyta = VerifyTAInterface(verifyta_path=config["verifyta_path"], do_print=False)

    trace_file_path = config["random_trace_file_path"]
    trace_file_path_base = trace_file_path.parent.joinpath(str(trace_file_path.stem)[:-1])
    settings = ['-o', '2', '-t', '0', '-Y', '-X', str(trace_file_path_base)]
    trace_file_path.unlink(missing_ok=True)

    output, is_timeout = verifyta.execute_verifyta(
        model_file_path=config["random_trace_generator_model_file_path"],
        output_dir_path=config["output_dir_path"], settings=settings)

    is_success = "-- Formula is satisfied." in output
    return is_success


def extract_deterministic_trace(config, symbolic_trace):
    """Extracts a "deterministic" trace from the symbolic trace, i.e., a trace where each edge transition is taken at a
       single distinct time instead of an interval of possible times.

    Args:
        config: The configration data for concrete transition times.
        symbolic_trace: The input trace for which a "deterministic" trace should be generated.

    Returns:
        The "deterministic" trace.
    """

    do_print = False
    current_dbm = symbolic_trace.init_state.dbm.copy()
    concrete_states = []
    global_tr_clock_index = current_dbm.clocks.index(f'sys._TR')

    for transition in symbolic_trace.transitions:
        source_dbm = transition.source_state.dbm
        target_dbm = transition.target_state.dbm
        delayed_dbm = transition.intermediate_states["delay_state"].dbm
        if do_print:
            print(f'---------------------------------')
            print(f'Source DBM:\n{source_dbm}')
            print(f'Delayed DBM:\n{delayed_dbm}')
            print(f'Target DBM:\n{target_dbm}')
            triggered_edges = [pe[0] + ": " + pe[1].source.name + " -> " +
                               pe[1].target.name for pe in transition.triggered_edges.items()]
            print(f'Triggered edges:\n{triggered_edges}')

        # Derive a helper DBM from the current DBM, and intersect it with the delayed DBM to apply its guards
        helper_dbm = current_dbm.copy()
        helper_dbm.intersect(delayed_dbm)

        if do_print:
            print(f'Helper DBM for selecting a concrete leaving time:\n{helper_dbm}')

        # From the resulting valid time interval of TG, select a concrete time for leaving the location
        valid_time_interval = helper_dbm.get_interval("sys._TG")
        lower_valid_leaving_time_bound = valid_time_interval.lower_val if valid_time_interval.lower_incl \
            else valid_time_interval.lower_val + 1
        upper_valid_leaving_time_bound = valid_time_interval.lower_val + 10 if valid_time_interval.upper_val == np.inf \
            else (valid_time_interval.upper_val if valid_time_interval.upper_incl
                  else valid_time_interval.upper_val - 1)
        selected_leaving_time = None
        if lower_valid_leaving_time_bound <= upper_valid_leaving_time_bound:
            if config["concrete_transition_times"] == "min":
                selected_leaving_time = lower_valid_leaving_time_bound
            elif config["concrete_transition_times"] == "max":
                selected_leaving_time = upper_valid_leaving_time_bound
            elif config["concrete_transition_times"] == "random":
                selected_leaving_time = random.randint(lower_valid_leaving_time_bound, upper_valid_leaving_time_bound)
            else:
                raise Exception('The "concrete_transition_times" option must be set to one of '
                                '{"min", "max", "random"}.')
            if do_print:
                print(f'Selected leaving time: {selected_leaving_time}')

            # Apply the selected leaving time as upper bound to the current DBM to get the semi-symbolic state
            current_dbm.conjugate(DBMConstraint(constr_text=f'sys._TG <= {selected_leaving_time}'))
        current_dbm.close()
        assert not current_dbm.is_empty(), f'The following DBM is empty:\n{current_dbm}'
        assert source_dbm.includes(current_dbm), f'The following DBM:\n{source_dbm}\ndoes not include:\n{current_dbm}'

        # Add the semi-symbolic state to the state list
        concrete_state = transition.source_state.copy()
        concrete_state.dbm = current_dbm.copy()
        concrete_states.append(concrete_state)

        # Set the current DBM to the helper DBM (to which the guards were already applied), and apply the selected
        # leaving time as upper bound here as well
        current_dbm = helper_dbm
        if selected_leaving_time:
            current_dbm.conjugate(DBMConstraint(constr_text=f'sys._TG <= {selected_leaving_time}'))

        # Determine the clocks that are reset during the transition
        relevant_reset_clock_indices = [i for i in range(2, len(target_dbm.matrix))
                                        if (target_dbm.matrix[i][global_tr_clock_index].val == 0 and
                                            target_dbm.matrix[global_tr_clock_index][i].val == 0)]
        relevant_reset_clocks = [source_dbm.clocks[i] for i in relevant_reset_clock_indices]

        # Apply selected leaving time as lower bound for transitions, perform resets accordingly, perform delay,
        # and intersect with the original target DBM to include the invariant constraints of the target locations
        if selected_leaving_time:
            current_dbm.conjugate(DBMConstraint(constr_text=f'sys._TG >= {selected_leaving_time}'))
        current_dbm.close()
        if do_print:
            print(f'Current DBM after TG lower bound (and close):\n{current_dbm}')
        assert not current_dbm.is_empty(), f'The following DBM is empty:\n{current_dbm}'
        assert source_dbm.includes(current_dbm), f'The following DBM:\n{source_dbm}\ndoes not include:\n{current_dbm}'

        for clock in relevant_reset_clocks:
            current_dbm.reset(clock)
        if do_print:
            print(f'Resetting clocks: {relevant_reset_clocks}')
            print(f'Current DBM after resets:\n{current_dbm}')

        current_dbm.delay_future()
        if do_print:
            print(f'Current DBM after DF:\n{current_dbm}')

        current_dbm.intersect(target_dbm)
        if do_print:
            print(f'Current DBM at loop iteration end (after intersect):\n{current_dbm}')
        assert not current_dbm.is_empty(), f'The following DBM is empty:\n{current_dbm}'
        assert target_dbm.includes(current_dbm), f'The following DBM:\n{target_dbm}\ndoes not include:\n{current_dbm}'

    # Create the final state (if necessary)
    if symbolic_trace.transitions:
        concrete_state = symbolic_trace.transitions[-1].target_state.copy()
        concrete_state.dbm = current_dbm.copy()
        concrete_states.append(concrete_state)

    # Create the concrete trace
    concrete_transitions = []
    triggered_edge_trace = [tr.triggered_edges for tr in symbolic_trace.transitions]
    for concrete_source_state, concrete_target_state, triggered_edges in \
            zip(concrete_states[:-1], concrete_states[1:], triggered_edge_trace):
        concrete_transition = Transition(
            source_state=concrete_source_state, target_state=concrete_target_state, triggered_edges=triggered_edges)
        concrete_transitions.append(concrete_transition)

    deterministic_trace = Trace(init_state=concrete_states[0], transitions=concrete_transitions)

    return deterministic_trace


def extract_data_points_from_deterministic_trace(deterministic_trace):
    """Extracts concrete data points from a "deterministic" trace.

    Args:
        deterministic_trace: The "deterministic" trace.

    Returns:
        The extracted data points / observation sequence.
    """
    data_points = []
    for state in deterministic_trace.get_states():
        valid_time_interval = state.dbm.get_interval("sys._TG")
        lower_time_bound = valid_time_interval.lower_val if valid_time_interval.lower_incl \
            else valid_time_interval.lower_val + 1
        upper_time_bound = valid_time_interval.lower_val + 10 if valid_time_interval.upper_val == np.inf else \
            (valid_time_interval.upper_val if valid_time_interval.upper_incl else valid_time_interval.upper_val - 1)
        if lower_time_bound <= upper_time_bound:
            selected_time = random.randint(lower_time_bound, upper_time_bound)

            data_point = {"t": selected_time, "vars": {}, "locs": {}}
            for key, val in state.vars.items():
                new_key = key.replace("sys.", "") if key.startswith("sys.") else key
                data_point["vars"][new_key] = val
            for proc, loc in state.locs.items():
                data_point["locs"][proc] = {
                    "name": loc.name if loc.name else None,
                    "is_committed": loc.committed
                }
            data_points.append(data_point)

    return data_points

