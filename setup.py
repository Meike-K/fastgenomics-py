#!/usr/bin/env python
import sys
import pip

from setuptools import setup
from distutils.version import LooseVersion

VERSION = '0.6.0'  # scheme: breaking major, non-breaking feature, fix


# check python and pip versions
if not sys.version_info[:2] >= (3, 6):
    sys.exit("Sorry - python < 3.6 not supported. Your version is: " + str(sys.version_info))

if not LooseVersion(pip.__version__).version[0] >= 6:
    sys.exit("Sorry - pip >= 6.0.0 is required. Your version is: " + str(pip.__version__))


# parse requirements with pip
dependency_links = []
install_requires = []

parsed_requirements = pip.req.parse_requirements('requirements.txt', session=pip.download.PipSession())

for item in parsed_requirements:
    # old pip: get url
    if getattr(item, 'url', None):
        dependency_links.append(str(item.url))
    # new pip: get link
    if getattr(item, 'link', None):
        dependency_links.append(str(item.link))
    if item.req:
        install_requires.append(str(item.req))

setup(name='FASTGenomics',
      version=VERSION,
      description='FASTGenomics python helper',
      author='FASTGenomics Team',
      author_email='contact@fastgenomics.org',
      url='https://github.com/fastgenomics/fastgenomics-py',
      packages=['fastgenomics'],
      package_data={'fastgenomics': ['schemes/*.json', 'templates/*.j2']},
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      dependency_links=dependency_links)
