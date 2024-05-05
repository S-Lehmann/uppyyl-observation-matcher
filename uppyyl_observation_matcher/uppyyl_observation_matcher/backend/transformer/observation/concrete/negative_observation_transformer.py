"""The negative observation transformer."""
import random

from uppyyl_observation_matcher.backend.transformer.observation.base_observation_transformer import \
    ObservationTransformer


INT16_MAX = 32767

class NegativeObservationTransformer(ObservationTransformer):
    """A transformer for generated observations."""

    def __init__(self, config, reference_trace):
        """Initializes GeneratedObservationTransformer."""
        super().__init__()

        self.config = config
        self.reference_trace = reference_trace

    def transform_data_points(self, observation):
        pass

    def transform_observation(self, observation):
        negative_transformation_types = ["var", "time"]
        selected_transformation_type = random.choice(negative_transformation_types)
        if selected_transformation_type == "time":
            observation[-1]["t"] = observation[-2]["t"] - (self.config["allowed_deviations"]["t"]*2+1)
        if selected_transformation_type == "var":
            for var_name in observation[-1]["vars"].keys():
                if var_name not in self.config["allowed_deviations"]:
                    continue
                observation[-1]["vars"][var_name] = int(INT16_MAX - (self.config["allowed_deviations"][var_name]+1))

