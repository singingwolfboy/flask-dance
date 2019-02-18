Contributing to Flask-Dance
===========================

If you want to contribute to Flask-Dance, we would love the help!

Providers
---------

The simplest way to contribute to Flask-Dance is by adding new
pre-set OAuth providers. Check out the ``contrib`` directory
to see how to do that. Don't forget to check the README file
to see the requirements for getting your contribution merged!

Documentation
-------------

Contributing to the documentation is probably the best thing you can do
for Flask-Dance! OAuth is complicated, and the people using Flask-Dance
don't want to understand all the details. Writing clear, comprehensive
documentation will make everyone's lives easier.

Code
----

The general checklist for all code contributions is:

- Code
- Tests
- Docs
- Changelog

We strive for roughly 95% test coverage. Not every line needs to be tested,
but there should be a clear justification for untested lines in your pull
request. You can use `tox`_ to run the unit tests on multiple Python
versions locally, if you want.

Documenting changes is very important! Particularly when adding new features
or changing existing ones, if it isn't documented, no one will know that
it exists.

The changelog is important to people who are using an old version of
Flask-Dance, and want to upgrade to a more recent version.
In your pull request, add a bullet point to the "unreleased" section
of the changelog, describing what your change does.

Do not modify the version number in your pull request. The maintainer
will change the version number when releasing a new version of
Flask-Dance.

Don't be afraid to ask for help! If you have a code change you'd like to make,
and you don't know how to write the tests or the docs, you're welcome to
open a pull request anyway and ask for help with completing the remaining
steps. (Just don't expect your pull request to be merged until those steps
are complete!)

.. _tox: https://tox.readthedocs.io/