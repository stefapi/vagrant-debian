#!/usr/bin/env python
import os
import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 6, 0):
    sys.exit("Python 3.6.0 is the minimum required version")

PROJECT_ROOT = os.path.dirname(__file__)

with open(os.path.join(PROJECT_ROOT, "README.md")) as file_:
    long_description = file_.read()

with open('vagrant_debian/__init__.py', 'rb') as fid:
    for line in fid:
        line = line.decode('utf-8')
        if line.startswith('__version__'):
            version = line.strip().split()[-1][1:-1]
            break

setup(
    name="vagrant_debian",
    version=version,
    python_requires=">=3.6.0",
    description="Create vagrant virtualbox from Debian ISO cd",
    long_description=long_description,
    long_description_content_type="text/markdown",
    platforms = ['Linux'],
    install_requires=[
        "jinja2"
    ],
    url="https://github.com/apiou/vagrant-debian",
    author="Stephane APIOU",
    author_email="stephane@apiou.org",
    license="BSD-2",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Operating System",
        "Topic :: Utilities"
    ],
    message_extractors = {
        'vagrant_debian' : [
            ('**.py', 'python', None)
        ]
    },
    entry_points={
        'console_scripts': [
            'vagrant_debian = vagrant_debian:__main__'
        ]
    },

    packages=find_packages(),
    include_package_data=True,
)

