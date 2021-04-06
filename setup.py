import sys
import re
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, because outside the eggs aren't loaded
        import pytest

        errno = pytest.main(self.test_args)
        sys.exit(errno)


def is_requirement(line):
    line = line.strip()
    # Skip blank lines, comments, and editable installs
    return not (
        line == ""
        or line.startswith("--")
        or line.startswith("-r")
        or line.startswith("#")
        or line.startswith("-e")
        or line.startswith("git+")
        or ";" in line
    )


def get_requirements(path):
    with open(path) as f:
        lines = f.readlines()
    return [l.strip() for l in lines if is_requirement(l)]


version = ""
with open("flask_dance/__init__.py") as fd:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE
    ).group(1)

if not version:
    raise RuntimeError("Cannot find version information")


setup(
    name="Flask-Dance",
    version=version,
    description="Doing the OAuth dance with style using Flask, requests, and oauthlib",
    long_description=open("README.rst").read(),
    author="David Baumgold",
    author_email="david@davidbaumgold.com",
    url="https://github.com/singingwolfboy/flask-dance",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=get_requirements("requirements.txt"),
    tests_require=get_requirements("tests/requirements.txt"),
    extras_require={"sqla": ["sqlalchemy>=1.3.11"], "signals": ["blinker"]},
    cmdclass={"test": PyTest},
    entry_points={"pytest11": ["pytest_flask_dance = flask_dance.fixtures.pytest"]},
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Framework :: Flask",
        "Framework :: Pytest",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    zip_safe=False,
)
