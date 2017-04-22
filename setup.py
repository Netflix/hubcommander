"""
HubCommander
================

A Slack bot for GitHub organization management.

:copyright: (c) 2017 by Netflix, see AUTHORS for more
:license: Apache, see LICENSE for more details.
"""
import sys
import os.path

from setuptools import setup, find_packages

ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))

# When executing the setup.py, we need to be able to import ourselves, this
# means that we need to add the src/ directory to the sys.path.
sys.path.insert(0, ROOT)

about = {}
with open(os.path.join(ROOT, "__about__.py")) as f:
    exec(f.read(), about)


install_requires = [
    'boto3>=1.4.3',     # For KMS support
    'duo_client==3.0',
    'tabulate>=0.7.7',
    'validators>=0.11.1',
    'rtmbot==0.4.0'
]

tests_require = [
    'pytest==3.0.6',
    'slackclient==1.0.5'
]

setup(
    name=about["__title__"],
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__email__"],
    url=about["__uri__"],
    description=about["__summary__"],
    long_description=open(os.path.join(ROOT, 'README.md')).read(),
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'tests': tests_require,
    },
)
