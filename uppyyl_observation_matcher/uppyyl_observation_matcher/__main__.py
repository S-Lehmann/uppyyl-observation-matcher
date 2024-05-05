"""The main entry point of the Uppaal trace matcher module."""

import argparse
import ast
import pathlib

import uppyyl_observation_matcher.config as conf
from uppyyl_observation_matcher.backend.helper import parse_config_value


def parse_arguments():
    """Parses the main input arguments.

    Returns:
        The parsed input arguments.
    """
    parser = argparse.ArgumentParser(description='The Uppaal trace matcher.')

    parser.add_argument('--verifyta', dest="verifyta_path", type=pathlib.Path)

    parser.add_argument('-m', '--model', dest="original_model_file_path", type=pathlib.Path)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--csv', dest="csv_data_file_path", type=pathlib.Path)
    group.add_argument('--trace', type=ast.literal_eval)

    parser.add_argument('--header', type=ast.literal_eval)

    parser.add_argument('-o', '--outdir', dest="output_dir_path", type=pathlib.Path)

    parser.add_argument('--config')

    parser.add_argument('--perform-match', action='store_true')
    parser.add_argument('--check-locations', action='store_true')
    parser.add_argument('--check-committed', action='store_true')
    parser.add_argument('--allow-partial-observations', action='store_true')
    parser.add_argument('--allowed-delay', type=int)
    parser.add_argument('--allowed-deviation', type=ast.literal_eval)

    args = vars(parser.parse_args())
    print(args)

    return args


def compose_config(args):
    """
    Composes a config dict from the input arguments.
    Args:
        args: The input arguments object.

    Returns:
        The composed config dict.
    """
    config = {}  # copy.deepcopy(args)
    for key, val in conf.config["config"].items():
        config[key] = parse_config_value(val)
    config.update((k, v) for k, v in args.items() if (v not in [None, False]))
    return config


def main():
    """The main function."""
    args = parse_arguments()
    if args["config"]:
        conf.config.read(args["config"])
    conf.inject_config_to_dependencies()

    _config = compose_config(args)


if __name__ == '__main__':
    main()
