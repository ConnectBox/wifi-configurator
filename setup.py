#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=6.0',
                'ConfigObj',
                'jinja2',
                'pyric']

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="Edwin Steele",
    author_email='edwin@wordspeak.org',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="Utility for command line configuration of hostapd",
    entry_points={
        'console_scripts': [
            'wifi_configurator=wifi_configurator.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='wifi_configurator',
    name='wifi_configurator',
    packages=find_packages(include=['wifi_configurator']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/ConnectBox/wifi_configurator',
    version='1.1.1',
    zip_safe=False,
)
