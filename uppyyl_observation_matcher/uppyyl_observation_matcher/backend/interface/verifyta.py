"""The verifyta interface."""

import pathlib
import subprocess
from timeit import default_timer

from uppyyl_observation_matcher.backend.logger.logger import verifyta_log


class VerifyTAInterface:
    """The verifyta interface."""
    def __init__(self, verifyta_path, timeout=None, do_print=True):
        self.do_print = do_print
        self.verifyta_path = pathlib.Path(verifyta_path)
        self.timeout = timeout

    def execute_command(self, command_parts):
        """Executes a given command in a separate process.

        Args:
            command_parts: The parts of the command.

        Returns:
            The stdout results of the command execution.
        """
        # Spawn verifyta process
        process = subprocess.Popen(
            command_parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Obtain stdout and stderr output from the verifyta process
        is_timeout = False
        try:
            out, err = process.communicate(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            out, err = process.communicate()
            is_timeout = True
        out = out.decode("UTF-8")
        err = err.decode("UTF-8")

        # Print output
        if self.do_print:
            verifyta_log.debug(f'Uppaal output (stdout):\n{out}')
        if err:
            verifyta_log.debug(f'Uppaal output (stderr):\n{err}')

        return out, is_timeout

    def execute_verifyta(self, model_file_path, output_dir_path, query_file_path=None, settings=None):
        """Executes a verifyta command.

        Args:
            model_file_path: The path of the input model file.
            output_dir_path: The path of the output directory.
            query_file_path: The path of the input query file.
            settings: The settings for verifyta.

        Returns:
            The logged output of the verifyta call.
        """
        settings = settings if settings else []
        model_file_path = pathlib.Path(model_file_path)
        query_file_path = pathlib.Path(query_file_path) if query_file_path else None
        output_dir_path = pathlib.Path(output_dir_path)

        # Create the output directory
        output_dir_path.mkdir(parents=True, exist_ok=True)

        # Compose the verifyta command
        verifyta_command_parts = [str(self.verifyta_path)]
        verifyta_command_parts += settings
        verifyta_command_parts.append(str(model_file_path))
        if query_file_path:
            verifyta_command_parts.append(str(query_file_path))

        if self.do_print:
            if query_file_path:
                verifyta_log.debug(f'Executing queries of file "{query_file_path.name}" for model '
                                   f'"{model_file_path.name}" with verifyta ...')
            else:
                verifyta_log.debug(f'Executing queries of model "{model_file_path.name}" with verifyta ...')

        # Execute verifyta command and measure time
        start_time = default_timer()
        output, is_timeout = self.execute_command(command_parts=verifyta_command_parts)
        elapsed_time = default_timer() - start_time

        if self.do_print:
            if query_file_path:
                verifyta_log.debug(f'Executing queries of file "{query_file_path.name}" for model '
                                   f'"{model_file_path.name}" with verifyta ... finished '
                                   f'[Elapsed time: {elapsed_time:.3f}s]')
            else:
                verifyta_log.debug(f'Executing queries of model "{model_file_path.name}" with verifyta ... finished.'
                                   f' [Elapsed time: {elapsed_time:.3f}s]')

        return output, is_timeout
