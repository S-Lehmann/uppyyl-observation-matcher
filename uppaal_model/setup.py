#!/usr/bin/env python

"""setup.py: Controls the setup process using setuptools."""

import re

from setuptools import setup

version = re.search(
    r'^__version__\s*=\s*"(.*)"',
    open('uppaal_model/version.py').read(),
    re.M
).group(1)

with open("README.md", "rb") as f:
    long_description = f.read().decode("utf-8")

setup(
    name="uppaal_model",
    packages=["uppaal_model"],
    entry_points={
        "console_scripts": [
        ]
    },
    version=version,
    description="Uppaal model.",
    long_description=long_description,
    author="Sascha Lehmann",
    author_email="s.lehmann@tuhh.de",
    project_urls={
        'Affiliation': 'https://www.tuhh.de/sts',
    },
    url="",
    install_requires=[
        'uppaal_c_language',
        'colorama==0.4.4',
        'coverage==5.5',
        'lxml == 4.6.5',
        'pytest==7.1.2',
        'pytest-subtests==0.8.0',
    ],
)
