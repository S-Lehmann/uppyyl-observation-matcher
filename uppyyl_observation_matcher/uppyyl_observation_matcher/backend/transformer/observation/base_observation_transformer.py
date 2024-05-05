"""The abstract observation transformer."""

import abc
import random


class ObservationTransformer(abc.ABC):
    """An abstract observation transformer."""

    def __init__(self):
        """Initializes ObservationTransformer."""
        self.output_model = None

    def transform(self, observation):
        """Applies the transformation ta a given observation sequence.

        Args:
            observation: The observation sequence.
        """
        self.transform_observation(observation=observation)
        self.transform_data_points(observation=observation)

    def transform_data_points(self, observation):
        """Applies transformations to the individual data points of an observation sequence.

        Args:
            observation: The observation sequence.
        """
        pass

    def transform_observation(self, observation):
        """Applies transformations to the observation sequence as a whole.

        Args:
            observation: The observation sequence.
        """
        pass


########################################################################################################################

############################
# Data points #
############################

# Partial observations (variables) ###
def reduce_data_point_to_selected_vars(data_point, var_names, set_removed_to_none=False):
    """Reduces the given data point to a selected subset of its contained variables.

    Args:
        data_point: The given data point.
        var_names: The list of variables to keep during reduction.
        set_removed_to_none: Flag specifying whether the non-selected variables should be removed from the data point
                             dict, or set to None instead.
    """
    for key in list(data_point["vars"].keys()):
        if key not in var_names:
            if set_removed_to_none:
                data_point["vars"][key] = None
            else:
                del data_point["vars"][key]


def reduce_data_point_to_random_vars(data_point, var_count_bounds, set_removed_to_none=False):
    """Reduces the given data point to a random subset of its contained variables.

    Args:
        data_point: The given data point.
        var_count_bounds: The tuple (lower_bound, upper_bound) specifying the range among which the amount of kept
                          variables is randomly selected.
        set_removed_to_none: Flag specifying whether the non-selected variables should be removed from the data point
                             dict, or set to None instead.
    """
    lower_bound = var_count_bounds[0] if var_count_bounds[0] is not None else 0
    upper_bound = var_count_bounds[1] if var_count_bounds[1] is not None else len(data_point["vars"])
    var_names = list(data_point["vars"].keys())
    selected_var_count = random.randint(lower_bound, upper_bound)
    selected_var_names = random.sample(var_names, selected_var_count)
    reduce_data_point_to_selected_vars(
        data_point=data_point, var_names=selected_var_names, set_removed_to_none=set_removed_to_none)


# Partial observations (locations) ###
def reduce_data_point_to_selected_process_locs(data_point, proc_names, set_removed_to_none=False):
    """Reduces the observed locations in a given data point to a selected subset of its processes.

    Args:
        data_point: The given data point.
        proc_names: The list of processes for which the observed locations should be kept during reduction.
        set_removed_to_none: A flag specifying whether the non-selected variables should be removed from the data point
                             dict, or set to None instead.
    """
    for key in list(data_point["locs"].keys()):
        if key not in proc_names:
            if set_removed_to_none:
                data_point["locs"][key] = None
            else:
                del data_point["locs"][key]


def reduce_data_point_to_random_locs(data_point, proc_count_bounds, set_removed_to_none=False):
    """Reduces the observed locations in a given data point to a random subset of its processes.

    Args:
        data_point: The given data point.
        proc_count_bounds: The tuple (lower_bound, upper_bound) specifying the range among which the amount of processes
                           kept for location observation is randomly selected.
        set_removed_to_none: A flag specifying whether the non-selected variables should be removed from the data point
                             dict, or set to None instead.
    """
    lower_bound = proc_count_bounds[0] if proc_count_bounds[0] is not None else 0
    upper_bound = proc_count_bounds[1] if proc_count_bounds[1] is not None else len(data_point["locs"]) - 1
    proc_names = list(data_point["locs"].keys())
    selected_proc_count = random.randint(lower_bound, upper_bound)
    selected_proc_names = random.sample(proc_names, selected_proc_count)
    reduce_data_point_to_selected_process_locs(
        data_point=data_point, proc_names=selected_proc_names, set_removed_to_none=set_removed_to_none)


# Deviating observations ###
def apply_random_deviations_to_data_point(data_point, bounds_dict, default_deviation_bounds):
    """Applies random deviations to the variable values in a data point.

    Args:
        data_point: The given data point.
        bounds_dict: A dict specifying the tuples (lower_bound, upper_bound) among which the actually applied deviations
                     for each variable are randomly selected.
        default_deviation_bounds: A tuple (lower_bound, upper_bound) specifying a default range among which the actually
                                  applied deviations for each variable are randomly selected if not specified in
                                  bounds_dict.
    """
    for key in list(data_point["vars"].keys()):
        if data_point["vars"][key] is None:
            continue
        if key in bounds_dict:
            lower_bound, upper_bound = bounds_dict[key]
        elif default_deviation_bounds:
            lower_bound, upper_bound = default_deviation_bounds
        else:
            lower_bound, upper_bound = (0, 0)
        selected_deviation = random.randint(lower_bound, upper_bound)
        selected_deviation_sign = random.choice([1, -1])
        data_point["vars"][key] += selected_deviation * selected_deviation_sign


# Time-shifted observations ###
def apply_time_shift_to_observation(observation, time_shift):
    """Applies a given time shift to all data points in an observation sequence.

    Args:
        observation: The given observation sequence.
        time_shift: The selected time shift.
    """
    for data_point in observation:
        data_point["t"] += time_shift


def apply_random_time_shift_to_observation(observation, time_shift_bounds):
    """Applies a random time shift to all data points in an observation sequence.

    Args:
        observation: The given observation sequence.
        time_shift_bounds: The tuple (lower_bound, upper_bound) specifying the range among which the actually applied
                           time shift is randomly selected.
    """
    lower_bound, upper_bound = time_shift_bounds
    if lower_bound < 0 or upper_bound < 0:
        raise Exception("Time shift between model and observation must be positive or zero.")
    selected_time_shift = -random.randint(lower_bound, upper_bound)
    apply_time_shift_to_observation(observation=observation, time_shift=selected_time_shift)


def remove_data_points_with_negative_time(observation):
    """Removes all data points that got a negative time value after a time shift (as these have not been observed)
       from an observation sequence.

    Args:
        observation: The given observation sequence.
    """
    shift = 0
    for idx, data_point in enumerate(observation.copy()):
        if data_point["t"] < 0:
            del observation[idx - shift]
            shift += 1


# Committed location observations ###
def remove_committed_states_from_observation(observation):
    """Removes all data points containing committed locations from an observation sequence.

    Args:
        observation: The given observation sequence.
    """
    shift = 0
    for idx, data_point in enumerate(observation.copy()):
        for proc_name, loc_data in data_point["locs"].items():
            if loc_data["is_committed"]:
                del observation[idx - shift]
                shift += 1
                break


# Reduced observations ###
def reduce_observation_to_selected_data_points(observation, data_point_indices):
    """Reduces a given observation sequence to a number of selected data points identified by their indices.

    Args:
        observation: The given observation sequence.
        data_point_indices: The list of data point indices which should be kept during reduction.
    """
    indices_to_delete = sorted(list(set(range(0, len(observation))).difference(set(data_point_indices))))
    shift = 0
    for idx in indices_to_delete:
        del observation[idx - shift]
        shift += 1


def reduce_observation_to_n_random_data_points(observation, n, keep_first=False, keep_last=False):
    """Reduces a given observation sequence to n randomly selected data points.

    Args:
        observation: The given observation sequence.
        n: THe number of randomly chosen data points to keep during reduction.
        keep_first: A flag specifying if the first data point in the observation sequence should necessarily be kept.
        keep_last: A flag specifying if the last data point in the observation sequence should necessarily be kept.
    """
    all_indices = list(range(0, len(observation)))
    indices_to_keep = []
    if keep_first:
        indices_to_keep.append(all_indices[0])
        del all_indices[0]
        n -= 1
    if keep_last:
        indices_to_keep.append(all_indices[-1])
        del all_indices[-1]
        n -= 1
    selected_indices = sorted(random.sample(all_indices, min(n, len(all_indices))) + indices_to_keep)

    reduce_observation_to_selected_data_points(observation=observation, data_point_indices=selected_indices)
