#! /usr/bin/env python

# Standard library
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="astrostamps",
    version='0.1',
    author="Semyeong Oh & Johnny Greco",
    author_email="jgreco@astro.princeton.edu",
    packages=["astrostamps"],# "astrostamps.tests"],
    url="https://github.com/johnnygreco/astrostamps",
    license="MIT",
    description="An astronomy stamp factory",
    #long_description=rd("README.md"),
    package_data={},
    install_requires=[],
    # include_package_data=True,
)
