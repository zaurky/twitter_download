#!/usr/bin/env python
from os import path

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

README = path.abspath(path.join(path.dirname(__file__), 'README.md'))
desc = 'A Python util to easily get pics from twitter'

setup(
    name='download_twitter',
    version='0.0.1',
    author='Zaurky',
    author_email='zaurky@zeb.re',
    description=desc,
    long_description=open(README).read(),
    license='GPLV2',
    url='http://github.com/zaurky/twitter_download',
    packages=['download_twitter'],
    install_requires=[
        'pexif>=0.13',
        'requests>=1.2.3',
        'requests-oauthlib>=0.3.2',
        'twython>=3.0.0',
        'vine_dwl',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)
