Pre-set Configurations
======================
This directory contains pre-set consumer configurations for
several popular OAuth providers. Have one that you'd like to add? Great, we
love pull requests! However, you must meet certain critera for your
configuration to accepted:

# You must create a Python file in this directory named after the service:
  for example, ``my_service.py``.
# The file must declare a ``__maintainer__`` variable, with the name and
  email address of the maintainer of this configuration.
# The file must have a factory function that returns an instance of an
  OAuth1ConsumerBlueprint or an instance of an OAuth2ConsumerBlueprint.
  The factory function must be named after the service: for example,
  ``make_my_service_blueprint()``.
# The file must expose a variable named after the service, which is a local
  proxy to the ``session`` attribute on the blueprint returned by the
  factory function.
# You must create a Python file in the ``tests/contrib`` directory named
  after your service with a prefix of ``test_``:
  for example, ``test_my_service``. This file must contain tests
  for the file you created in this directory.
# You must add your configuration to the ``docs/contrib.rst`` file, and ensure
  that your factory function has a RST-formatted docstring that the
  documentation can pick up.
# All automated tests must pass, and the test coverage must not drop.
