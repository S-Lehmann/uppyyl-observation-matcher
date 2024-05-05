"""The edge trace simulator."""

from uppyyl_observation_matcher.backend.helper import save_model_to_file, load_trace_from_file
from uppyyl_observation_matcher.backend.interface.verifyta import VerifyTAInterface
from uppyyl_observation_matcher.backend.transformer.model.concrete.transition_simulator_model_transformer import \
    TransitionSimulatorModelTransformer
from uppyyl_observation_matcher.backend.transformer.trace.concrete.transition_simulator_model_trace_transformer import \
    TransitionSimulatorModelTraceTransformer


class EdgeTraceSimulator:
    """The edge trace simulator."""

    def __init__(self, config, model, instance_data):
        self.config = config
        self.input_model = None
        self.instance_data = None
        self.transition_simulator_model = None
        self.set_model(model=model, instance_data=instance_data)

    def simulate_edge_trace(self, edge_trace):
        """Simulated an edge trace, i.e., performs a model run based on given edge activation data.

        Args:
            edge_trace: The edge trace containing the activation data of edges.

        Returns:
            The simulated trace.
        """
        self.create_transition_simulator_model(edge_trace=edge_trace)
        is_success = perform_trace_simulation_with_uppaal(self.config)
        if is_success:
            transition_simulator_model_trace = load_trace_from_file(
                trace_file_path=self.config["transition_simulator_trace_file_path"],
                system=self.transition_simulator_model)
            simulated_trace = transform_transition_simulator_model_trace_to_original_domain(
                transition_simulator_model_trace=transition_simulator_model_trace,
                transition_simulator_model=self.transition_simulator_model, original_model=self.input_model
            )
        else:
            simulated_trace = None

        return is_success, simulated_trace

    def create_transition_simulator_model(self, edge_trace):
        """Creates the transition simulator model.

        Args:
            edge_trace: The edge trace containing the activation data of edges.
        """
        transition_simulator_model_transformer = TransitionSimulatorModelTransformer()
        transition_simulator_model_transformer.set_instance_data(instance_data=self.instance_data)
        transition_simulator_model_transformer.set_edge_trace(edge_trace=edge_trace)

        self.transition_simulator_model = self.input_model.copy()
        transition_simulator_model_transformer.transform(model=self.transition_simulator_model)
        save_model_to_file(model=self.transition_simulator_model,
                           model_path=self.config["transition_simulator_model_file_path"])

    def set_model(self, model, instance_data):
        """Sets the model for which the edge trace should be simulated.

        Args:
            model: The source model.
            instance_data: The instance data of the model.
        """
        self.input_model = model
        self.instance_data = instance_data
        self.transition_simulator_model = None


########################################################################################################################
# Functions #
########################################################################################################################

def perform_trace_simulation_with_uppaal(config):
    """Performs trace simulation with Uppaal verifyta.

    Args:
        config: The configuration data for verifyta.

    Returns:
        The trace simulation result.
    """
    verifyta = VerifyTAInterface(verifyta_path=config["verifyta_path"], do_print=False)

    trace_file_path = config["transition_simulator_trace_file_path"]
    trace_file_path_base = trace_file_path.parent.joinpath(str(trace_file_path.stem)[:-1])
    settings = ['-t', '0', '-X', str(trace_file_path_base)]
    trace_file_path.unlink(missing_ok=True)

    output, is_timeout = verifyta.execute_verifyta(
        model_file_path=config["transition_simulator_model_file_path"],
        output_dir_path=config["output_dir_path"], settings=settings)

    is_success = "-- Formula is satisfied." in output
    return is_success


def transform_transition_simulator_model_trace_to_original_domain(
        transition_simulator_model_trace, transition_simulator_model, original_model):
    """Transforms the transition simulator model trace to a corresponding trace in the original model domain.

        Args:
            transition_simulator_model_trace: The transition simulator model trace which should be transformed.
            transition_simulator_model: The transition simulator model (i.e., the source domain of the trace).
            original_model: The original model (i.e., the target domain of the trace).

        Returns:
            The transformed trace.
        """
    simulated_model_trace = transition_simulator_model_trace.copy()
    trace_transformer = TransitionSimulatorModelTraceTransformer(
        source_system=transition_simulator_model, target_system=original_model)
    trace_transformer.transform(trace=simulated_model_trace)
    return simulated_model_trace
