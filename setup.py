#!/usr/bin/env python3

# Copyright (C) 2024 RidgeRun, LLC (http://www.ridgerun.com)
# All Rights Reserved.

# The contents of this software are proprietary and confidential to RidgeRun,
# LLC.  No part of this program may be photocopied, reproduced or translated
# into another programming language without prior written consent of
# RidgeRun, LLC.  The user is free to modify the source code after obtaining
# a software license from RidgeRun.  All source code changes must be provided
# back to RidgeRun without any encumbrance.

from setuptools import setup, find_packages
from os import path
import unittest

here = path.abspath(path.dirname(__file__))

# automatically use README.md as long_description
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

# automatically detect tests


def web_model_server_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('web_model_server', pattern='test_*.py')
    return test_suite


setup(
    name='web_model_server',
    version='0.1.0',
    description=("Web Model Server for interface"),
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ridgerun-ai/web-model-server',
    author='RidgeRun',
    author_email='support@ridgerun.com',
    # Exclude the tests from the distribution package
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    # Included scripts should be in the bin folder
    scripts=['bin/apply_to_video', 'bin/apply_to_image', 'bin/run_gui'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Programming Language :: Python :: 3.8',
        "License :: Other/Proprietary License",
    ],
    python_requires='>=3.8',
    # Package dependencies
    install_requires=required,
    # tests module name
    test_suite='setup.web_model_server_test_suite'
)
