#
# This file is part of the RapidMiner Python package.
#
# Copyright (C) 2018-2021 RapidMiner GmbH
#
# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU Affero General Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with this program.
# If not, see https://www.gnu.org/licenses/.
#
from setuptools import setup, find_packages
import os
import codecs
import re

requirements = ["pandas", "requests", "numpy", "zeep", "h5py", "tink"]
name = "rapidminer"
here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

version = find_version(name, "__init__.py")
readme = ""
try:
    readme = read("..", "..", "..", "..", "README.md")
except FileNotFoundError:
    try:
        # different repositories may have at a different path
        readme = read("README.md")
    except FileNotFoundError:
        # ignore
        pass

# Replaces links to other markdown files with github links to make them work on PyPi
github_baseurl = "https://github.com/rapidminer/python-rapidminer/blob/" + version + "/"
for cname in "Studio.md", "Server.md", "Scoring.md", "Project.md" "Connections.md":
    readme = readme.replace("docs/api/" + cname, github_baseurl + "docs/api/" + cname)
for pyname in "studio_examples.ipynb", "server_examples.ipynb":
    readme = readme.replace("examples/" + pyname, github_baseurl + "examples/" + pyname)
    
setup(name=name,
      version=version,
      description='Tools for running RapidMiner processes and managing RapidMiner repositories.',
      url='https://github.com/rapidminer/python-rapidminer',
      author='RapidMiner',
      license='AGPL',
      long_description=readme,
      long_description_content_type="text/markdown",
      packages=find_packages(),
      zip_safe=False,
      install_requires=requirements,
      python_requires='>=3')
