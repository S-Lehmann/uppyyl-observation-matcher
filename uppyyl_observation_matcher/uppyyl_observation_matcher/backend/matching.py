"""The observation matcher."""
import warnings

from uppyyl_observation_matcher.backend.helper import load_trace_from_file, save_model_to_file
from uppyyl_observation_matcher.backend.logger.log_time import log_time
from uppyyl_observation_matcher.backend.interface.verifyta import VerifyTAInterface
from uppyyl_observation_matcher.backend.transformer.model.concrete.extended_matcher_model_transformer import \
    ExtendedMatcherModelTransformer
from uppyyl_observation_matcher.backend.transformer.model.concrete.raw_matcher_model_transformer import \
    RawMatcherModelTransformer
from uppyyl_observation_matcher.backend.transformer.trace.concrete.extended_matcher_model_trace_transformer import \
    ExtendedMatcherModelTraceTransformer


class ObservationMatcher:
    """The observation matcher."""

    def __init__(self, config, model, instance_data, observation_data=None, matcher_type="B", timeout=None):
        self.config = config
        self.input_model = None
        self.instance_data = None
        self.observation_data = None
        self.matcher_type = matcher_type
        self.matcher_model_transformer = None
        self.timeout = timeout

        self._prepared_matcher_model = None
        self.matcher_model = None

        self.set_model(model=model, instance_data=instance_data)
        self.set_matcher_type(matcher_type=matcher_type)

        if observation_data is not None:
            self.set_observation_data(observation_data=observation_data)

    @log_time
    def match(self, observation_data=None, return_trace=False, use_existing_matcher=False, use_prepared=False,
              time_log=None):
        """Performs matching of given observation data on the traces of a model.

        Args:
            observation_data: The observation sequence.
            return_trace: A flag indicating whether the matched trace should be returned.
            use_existing_matcher: A flag indicating whether an existing matcher should be used (or whether it should
                                  be generated anew).
            use_prepared: A flag indicating whether the initially prepared version of the matcher should be used
                          (or whether it should be generated anew).
            time_log: An optional dict used for logging time data.

        Returns:

        """
        if observation_data is not None:
            self.set_observation_data(observation_data=observation_data)
        if use_existing_matcher and self.matcher_model is None:
            warnings.warn("Instructed to use existing matcher model, but model was not generated yet. "
                          "Generating matcher model.")
            self.create_matcher_model(use_prepared=use_prepared)
        if not use_existing_matcher:
            self.create_matcher_model(use_prepared=use_prepared)

        is_matching, is_timeout = perform_matching_with_uppaal(
            config=self.config, timeout=self.timeout, log_time_to=(time_log, "matching"))

        if is_matching and return_trace:
            matcher_model_trace = load_trace_from_file(
                trace_file_path=self.config["matcher_model_trace_file_path"], system=self.matcher_model)
            matching_trace = transform_matcher_model_trace_to_original_domain(
                matcher_model_trace=matcher_model_trace, matcher_model=self.matcher_model,
                original_model=self.input_model
            )
        else:
            matching_trace = None

        res = {
            "is_matching": is_matching,
            "is_timeout": is_timeout,
            "matching_trace": matching_trace
        }
        return res

    def prepare_matcher_model(self):
        """Prepares the matcher model."""
        self.matcher_model = None
        self._prepared_matcher_model = self.input_model.copy()
        self.matcher_model_transformer.prepare(model=self._prepared_matcher_model)

    def create_matcher_model(self, use_prepared=False):
        """Creates the matcher model (potentially based on the prepared version of the matcher model).

        Args:
            use_prepared: A flag indicating whether the prepared matcher model version should be used.
        """
        if use_prepared and not self._prepared_matcher_model:
            warnings.warn("Instructed to use prepared matcher model, but model was not prepared yet. "
                          "Preparing matcher model.")
        if not use_prepared or not self._prepared_matcher_model:
            self.prepare_matcher_model()
        else:
            print("Using prepared matcher model.")

        self.matcher_model = self._prepared_matcher_model.copy()
        self.matcher_model_transformer.finalize(model=self.matcher_model)
        save_model_to_file(model=self.matcher_model, model_path=self.config["matcher_model_file_path"])

    def set_model(self, model, instance_data):
        """Sets the model against which the observations should be matched.

        Args:
            model: The source model.
            instance_data: The instance data of the model.
        """
        self.input_model = model
        self.instance_data = instance_data
        self._prepared_matcher_model = None
        self.matcher_model = None
        self.observation_data = None
        if self.matcher_type:
            self.set_matcher_type(self.matcher_type)

    def set_observation_data(self, observation_data):
        """Sets the observation data which should be matched against the model.

        Args:
            observation_data: The observation data.
        """
        self.observation_data = observation_data
        if self.matcher_model_transformer:
            self.matcher_model_transformer.set_observation_data(observation_data=observation_data)

    def set_matcher_type(self, matcher_type):
        """Sets the matcher type (the raw matcher is used if the matcher type is "R", the extended matcher in all other
           cases).

        Args:
            matcher_type: The matcher type.
        """
        self.matcher_type = matcher_type
        if matcher_type == "R":
            self.matcher_model_transformer = RawMatcherModelTransformer(config=self.config)
        else:
            if not self.instance_data:
                raise Exception("Instance data needs to be set before setting the matcher type to non-raw.")
            self.matcher_model_transformer = ExtendedMatcherModelTransformer(config=self.config)
            self.matcher_model_transformer.set_instance_data(instance_data=self.instance_data)

        if self.observation_data:
            self.matcher_model_transformer.set_observation_data(observation_data=self.observation_data)


########################################################################################################################
# Functions #
########################################################################################################################

@log_time
def perform_matching_with_uppaal(config, timeout=None):
    """Performs matching with Uppaal verifyta.

    Args:
        config: The configuration data for verifyta.
        timeout: A timeout after which the matching process should be aborted.

    Returns:
        The matching result.
    """
    verifyta = VerifyTAInterface(verifyta_path=config["verifyta_path"], do_print=False, timeout=timeout)

    trace_file_path = config["matcher_model_trace_file_path"]
    trace_file_path_base = trace_file_path.parent.joinpath(str(trace_file_path.stem)[:-1])
    settings = ['-t', '0', '-X', str(trace_file_path_base)]
    trace_file_path.unlink(missing_ok=True)

    output, is_timeout = verifyta.execute_verifyta(
        model_file_path=config["matcher_model_file_path"], output_dir_path=config["output_dir_path"], settings=settings)
    is_satisfied = "-- Formula is satisfied." in output
    return is_satisfied, is_timeout


def transform_matcher_model_trace_to_original_domain(matcher_model_trace, matcher_model, original_model):
    """Transforms the matcher model trace to a corresponding trace in the original model domain.

    Args:
        matcher_model_trace: The matcher model trace which should be transformed.
        matcher_model: The matcher model (i.e., the source domain of the trace).
        original_model: The original model (i.e., the target domain of the trace).

    Returns:
        The transformed trace.
    """
    original_domain_trace = matcher_model_trace.copy()
    trace_transformer = ExtendedMatcherModelTraceTransformer(source_system=matcher_model, target_system=original_model)
    trace_transformer.transform(trace=original_domain_trace)
    return original_domain_trace
