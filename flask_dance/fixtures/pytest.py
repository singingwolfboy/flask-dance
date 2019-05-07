"""
Flask-Dance provides a handy Pytest_ fixture named
``betamax_record_flask_dance`` that wraps Flask-Dance
sessions with Betamax_ to record and replay HTTP requests.
In order to use this fixture, you must install Betamax in your testing
environment. You must also define two other Pytest fixtures:
``app`` and ``flask_dance_sessions``. The ``app`` fixture must
return the Flask app that is being tested, and the
``flask_dance_sessions`` fixture must return the Flask-Dance
session or sessions that should be wrapped using Betamax.

For example:

.. code-block:: python

    from flask_dance.contrib.github import github
    from myapp import app as _app


    @pytest.fixture
    def app():
        return _app


    @pytest.fixture
    def flask_dance_sessions():
        return github

The ``flask_dance_sessions`` fixture can return either a single
session, or a list/tuple of sessions.

To use this fixture, it's generally easiest to decorate your test
with :func:`pytest.mark.usefixtures`, like this:

.. code-block:: python
    :emphasize-lines: 1

    @pytest.mark.usefixtures("betamax_record_flask_dance")
    def test_home_page(app):
        with app.test_client() as client:
            response = client.get("/", base_url="https://example.com")
        assert response.status_code == 200

"""
from __future__ import absolute_import

import pytest

try:
    from betamax import Betamax
except ImportError:
    Betamax = None


@pytest.fixture
def betamax_record_flask_dance(app, flask_dance_sessions, request):
    """
    Wraps the specified Flask-Dance sessions with Betamax

    This allows you to record and re-play HTTP requests from Flask-Dance
    sessions. Requires the Betamax library. You must also define a
    `flask_dance_sessions` fixture, that defines the session or sessions
    that should be wrapped with Betamax.
    """
    if not Betamax:
        raise ImportError(
            "The `betamax_record_flask_dance` fixture depends on "
            "the `betamax` module"
        )

    if isinstance(flask_dance_sessions, (list, tuple)):
        betamax_setup_info = [
            (
                session,
                "{testname}-{index}".format(testname=request.node.name, index=index),
            )
            for index, session in enumerate(flask_dance_sessions)
        ]
    else:
        session = flask_dance_sessions
        betamax_setup_info = [(session, request.node.name)]

    @app.before_request
    def wrap_flask_dance_with_betamax():
        recorders = [
            Betamax(session).use_cassette(cassette_name)
            for session, cassette_name in betamax_setup_info
        ]
        for recorder in recorders:
            recorder.start()

        @app.after_request
        def unwrap(response):
            for recorder in recorders:
                recorder.stop()
            return response

        request.addfinalizer(lambda: app.after_request_funcs[None].remove(unwrap))

    request.addfinalizer(
        lambda: app.before_request_funcs[None].remove(wrap_flask_dance_with_betamax)
    )

    return app
