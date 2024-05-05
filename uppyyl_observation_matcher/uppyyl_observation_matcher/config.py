"""This module provides global configuration data for the complete package."""
import ast
import configparser
import pathlib

converters = {
    'dict': ast.literal_eval,
    'path': pathlib.Path,
}
config = configparser.ConfigParser(converters=converters)
config._interpolation = configparser.ExtendedInterpolation()


def inject_config_to_dependencies():
    """Injects the current state of global configuration data into dependent packages."""
    pass
