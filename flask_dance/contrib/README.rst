Pre-set Configurations
======================
This directory contains pre-set consumer configurations for
several popular OAuth providers. Have one that you'd like to add? Great, we
love pull requests! However, you must meet certain criteria for your
configuration to accepted:

1. You must create a Python file in this directory named after the provider:
   for example, ``my_provider.py``.
2. The file must declare a ``__maintainer__`` variable, with the name and
   email address of the maintainer of this configuration.
3. The file must have a factory function that returns an instance of
   OAuth1ConsumerBlueprint or an instance of OAuth2ConsumerBlueprint.
   The factory function must be named after the provider: for example,
   ``make_my_provider_blueprint()``.
4. The file must expose a variable named after the provider, which is a local
   proxy to the ``session`` attribute on the blueprint returned by the
   factory function.
5. You must create a Python file in the ``tests/contrib`` directory named
   after your provider with a prefix of ``test_``:
   for example, ``test_my_provider``. This file must contain tests
   for the file you created in this directory.
6. You must add your provider to the ``docs/providers.rst`` file, and ensure
   that your factory function has a RST-formatted docstring that the
   documentation can pick up.
7. All automated tests must pass, and the test coverage must not drop.
8. You must update the ``CHANGELOG.rst`` file to indicate that this provider
   was added.
