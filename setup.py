# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, Command, find_packages


class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys,subprocess
        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)


def is_requirement(line):
    line = line.strip()
    # Skip blank lines, comments, and editable installs
    return not (
        line == '' or
        line.startswith('-r') or
        line.startswith('#') or
        line.startswith('-e') or
        line.startswith('git+')
    )


def get_requirements(path):
    with open(path) as f:
        lines = f.readlines()
    return [l.strip() for l in lines if is_requirement(l)]


setup(
    name="Flask-Dance",
    version="0.4.0",
    description="Doing the OAuth dance with style using Flask, requests, and oauthlib",
    long_description=open('README.rst').read(),
    author="David Baumgold",
    author_email="david@davidbaumgold.com",
    url="https://github.com/singingwolfboy/flask-dance",
    packages=find_packages(),
    install_requires=get_requirements("requirements.txt"),
    tests_require=get_requirements("dev-requirements.txt"),
    extras_require={
        'models': ['sqlalchemy', 'sqlalchemy-utils'],
        'signals': ['blinker'],
    },
    cmdclass = {'test': PyTest},
    license='MIT',
    classifiers=(
        'License :: OSI Approved :: MIT License',
        'Framework :: Flask',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ),
    zip_safe=False,
)

