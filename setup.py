#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: python -*-
from setuptools import setup, find_packages

## See the following pages for keywords possibilities for setup keywords, etc.
# https://packaging.python.org/
# https://docs.python.org/3/distutils/apiref.html
# https://docs.python.org/3/distutils/setupscript.html

setup(name='bi-solr-sync',
      version='1.0',
      description='Script for extracting documents from Solr and formatting in a way the DWH solution understands',
      maintainer="metascrum",
      maintainer_email="metascrum@dbc.dk",
      packages=find_packages(where='src'),
      package_dir={'': 'src'},
      entry_points = {'console_scripts': ['reference-service=main:main']},
      provides=['service_ref'],
      install_requires=['argcomplete', 'requests', 'argparse'],
      include_package_data=True,
      zip_safe=False)
