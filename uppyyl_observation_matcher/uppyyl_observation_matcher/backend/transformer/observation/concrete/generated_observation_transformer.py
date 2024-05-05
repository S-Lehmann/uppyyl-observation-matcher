"""The transformer for generated observations."""

import random

from uppyyl_observation_matcher.backend.transformer.observation.base_observation_transformer import \
    ObservationTransformer, apply_random_deviations_to_data_point, reduce_data_point_to_selected_vars, \
    reduce_data_point_to_random_vars, reduce_observation_to_n_random_data_points, \
    apply_random_time_shift_to_observation, remove_committed_states_from_observation, \
    remove_data_points_with_negative_time


class GeneratedObservationTransformer(ObservationTransformer):
    """A transformer for generated observations."""

    def __init__(self, config, process_names):
        """Initializes GeneratedObservationTransformer."""
        super().__init__()

        self.config = config
        self.process_names = process_names

    def transform_data_points(self, observation):
        for data_point in observation:

            # Variable observations
            allow_variable_observations = self.config.get("allow_variable_observations", None)
            observed_variables = self.config.get("observed_variables", None)
            if allow_variable_observations:
                if observed_variables:
                    reduce_data_point_to_selected_vars(
                        data_point=data_point, var_names=observed_variables, set_removed_to_none=False)
            else:
                data_point["vars"] = {}

            # Partial observations
            allow_partial_observations = self.config.get("allow_partial_observations", None)
            if allow_partial_observations:
                reduce_data_point_to_random_vars(
                    data_point=data_point, var_count_bounds=(1, None), set_removed_to_none=True)

            # Deviating observations
            default_deviation_bounds = self.config.get("default_deviation_bounds", None)
            allowed_deviations_in_observations = self.config.get("allowed_deviations_in_observations", None)
            apply_random_deviations_to_data_point(data_point=data_point, bounds_dict=allowed_deviations_in_observations,
                                                  default_deviation_bounds=default_deviation_bounds)

            # Location observations
            allow_location_observations = self.config.get("allow_location_observations", None)
            observed_processes_for_locations = self.config.get("observed_processes_for_locations", None)
            if allow_location_observations:
                if observed_processes_for_locations:
                    reduce_data_point_to_selected_vars(
                        data_point=data_point, var_names=observed_processes_for_locations, set_removed_to_none=False)
            else:
                data_point["locs"] = {}

    def transform_observation(self, observation):
        # Time-shifted observations
        time_shift_bounds = self.config.get("time_shift_bounds", None)
        if time_shift_bounds:
            apply_random_time_shift_to_observation(observation=observation, time_shift_bounds=time_shift_bounds)
            remove_data_points_with_negative_time(observation=observation)

        # Committed location observations
        allow_committed_observations = self.config.get("allow_committed_observations", None)
        if not allow_committed_observations:
            remove_committed_states_from_observation(observation=observation)

        # Remove particular data points
        observation_count_bounds = self.config.get("observation_count_bounds", None)
        if observation_count_bounds:
            selected_observation_count = random.randint(observation_count_bounds[0], observation_count_bounds[1])
            force_keep_first_observation = self.config.get("force_keep_first_observation", None)
            force_keep_last_observation = self.config.get("force_keep_last_observation", None)

            reduce_observation_to_n_random_data_points(
                observation=observation, n=selected_observation_count,
                keep_first=force_keep_first_observation, keep_last=force_keep_last_observation)
