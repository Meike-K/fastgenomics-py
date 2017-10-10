#!/usr/bin/env python
import sys

if sys.version_info < (3, 6):
    sys.exit("Sorry - python < 3.6 not supported")

import pathlib
from setuptools import setup


VERSION = '0.2.0'  # scheme: breaking major, non-breaking feature, fix


with open(pathlib.Path(__file__).parent / 'requirements.txt') as f_req:
    REQUIREMENTS = [line for line in f_req.readlines() if not line.startswith('#')]


setup(name='FASTGenomics',
      version=VERSION,
      scripts=['fastgenomics/bin/check_my_app'],
      description='FASTGenomics python helper',
      author='FASTGenomics Team',
      author_email='contact@fastgenomics.org',
      url='https://github.com/fastgenomics/fastgenomics-py',
      packages=['fastgenomics'],
      package_data={'fastgenomics': ['schemes/*.json', 'templates/*.j2']},
      install_requires=REQUIREMENTS
      )
