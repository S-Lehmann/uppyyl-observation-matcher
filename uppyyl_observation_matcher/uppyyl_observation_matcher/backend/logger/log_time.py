"""A logger decorator for time logging."""

import inspect
from timeit import default_timer


def log_time(func):
    """A logger decorator for time logging."""
    def logged_func(*args, **kwargs):
        """The logged function.

        Args:
            *args: The list of arguments.
            **kwargs: The dict of keyword arguments.

        Returns:
            The returned data of the logged function.
        """
        if 'log_time_to' not in kwargs:
            func_return = func(*args, **kwargs)
            return func_return
        else:
            log_dict, log_name = kwargs['log_time_to']
            del kwargs['log_time_to']
            if not isinstance(log_dict, dict):
                func_return = func(*args, **kwargs)
                return func_return

            func_has_explicit_log = 'time_log' in inspect.getfullargspec(func)[0]
            if func_has_explicit_log:
                time_log = {}
                kwargs['time_log'] = time_log
                log_dict[log_name] = time_log

            start_time = default_timer()
            func_return = func(*args, **kwargs)
            end_time = default_timer()
            elapsed_time = end_time - start_time

            if func_has_explicit_log:
                log_dict[log_name]["total"] = elapsed_time
            else:
                log_dict[log_name] = elapsed_time
            return func_return

    return logged_func
