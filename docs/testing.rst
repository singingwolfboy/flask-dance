Testing Apps That Use Flask-Dance
=================================

Automated tests are a great way to keep your Flask app stable
and working smoothly. The Flask documentation has
:doc:`some great information on how to write automated tests
for Flask apps <flask:testing>`.

However, Flask-Dance presents some challenges for writing tests.
What happens when you have a view function that requires OAuth
authorization? How do you handle cases where the user has a valid
OAuth token, an expired token, or no token at all?
Fortunately, we've got you covered.

Mock Storages
-------------

The simplest way to write tests with Flask-Dance is to use a
mock token storage. This allows you to easily control
whether Flask-Dance believes the current user is authorized
with the OAuth provider or not. Flask-Dance provides two
mock token storages:

.. currentmodule:: flask_dance.consumer.storage

.. autoclass:: NullStorage

.. autoclass:: MemoryStorage

Let's say you are testing the following code::

    from flask import redirect, url_for
    from flask_dance.contrib.github import make_github_blueprint, github

    app = Flask(__name__)
    github_bp = make_github_blueprint()
    app.register_blueprint(github_bp, url_prefix="/login")

    @app.route("/")
    def index():
        if not github.authorized:
            return redirect(url_for("github.login"))
        return "You are authorized"

You want to write tests to cover two cases: what happens when the user
is authorized with the OAuth provider, and what happens when they are not.
Here's how you could do that with `pytest`_ and the :class:`MemoryStorage`:

.. code-block:: python
    :emphasize-lines: 6, 16

    from flask_dance.consumer.storage import MemoryStorage
    from myapp import app, github_bp

    def test_index_unauthorized(monkeypatch):
        storage = MemoryStorage()
        monkeypatch.setattr(github_bp, "storage", storage)

        with app.test_client() as client:
            response = client.get("/", base_url="https://example.com")

        assert response.status_code == 302
        assert response.headers["Location"] == "https://example.com/login/github"

    def test_index_authorized(monkeypatch):
        storage = MemoryStorage({"access_token": "fake-token"})
        monkeypatch.setattr(github_bp, "storage", storage)

        with app.test_client() as client:
            response = client.get("/", base_url="https://example.com")

        assert response.status_code == 200
        text = response.get_data(as_text=True)
        assert text == "You are authorized"

In this example, we're using the
`monkeypatch fixture <https://docs.pytest.org/en/latest/monkeypatch.html>`__
to set a mock storage on the Flask-Dance blueprint. This fixture will
ensure that the original storage is put back on the blueprint after the
test is finished, so that the test doesn't change the code being tested.
Then, we create a test client and access the ``index`` view.
The mock storage will control whether ``github.authorized`` is ``True``
or ``False``, and the rest of the test asserts that the result is what
we expect.

Mock API Responses
------------------

Once you've gotten past the question of whether the current user is
authorized or not, you still have to account for any API calls that
your view makes. It's usually a bad idea to make real API calls in an
automated test: not only does it make your tests run significantly
more slowly, but external factors like rate limits can affect whether
your tests pass or fail.

There are several other libraries that you can use to mock API responses,
but I recommend Betamax_. It's powerful, flexible, and it's designed
to work with Requests_, the HTTP library that Flask-Dance is built on.
Betamax is also created and maintained by one of the primary maintainers
of the Requests library, `@sigmavirus24`_.

Let's say your testing the same code as before, but now the ``index``
view looks like this::

    @app.route("/")
    def index():
        if not github.authorized:
            return redirect(url_for("github.login"))
        resp = github.get("/user")
        return "You are @{login} on GitHub".format(login=resp.json()["login"])

Here's how you could test this view using Betamax::

    import os
    from flask_dance.consumer.storage import MemoryStorage
    from flask_dance.contrib.github import github
    import pytest
    from betamax import Betamax
    from myapp import app as _app
    from myapp import github_bp

    with Betamax.configure() as config:
        config.cassette_library_dir = 'cassettes'

    @pytest.fixture
    def app():
        return _app

    @pytest.fixture
    def betamax_github(app, request):

        @app.before_request
        def wrap_github_with_betamax():
            recorder = Betamax(github)
            recorder.use_cassette(request.node.name)
            recorder.start()

            @app.after_request
            def unwrap(response):
                recorder.stop()
                return response

            request.addfinalizer(
                lambda: app.after_request_funcs[None].remove(unwrap)
            )

        request.addfinalizer(
            lambda: app.before_request_funcs[None].remove(wrap_github_with_betamax)
        )

        return app

    @pytest.mark.usefixtures("betamax_github")
    def test_index_authorized(app, monkeypatch):
        access_token = os.environ.get("GITHUB_OAUTH_ACCESS_TOKEN", "fake-token")
        storage = MemoryStorage({"access_token": access_token})
        monkeypatch.setattr(github_bp, "storage", storage)

        with app.test_client() as client:
            response = client.get("/", base_url="https://example.com")

        assert response.status_code == 200
        text = response.get_data(as_text=True)
        assert text == "You are @singingwolfboy on GitHub"

In this example, we first
:doc:`configure Betamax globally <betamax:configuring>`
so that it stores cassettes (recorded HTTP interactions) in the ``cassettes``
directory. Betamax expects you to commit these cassettes to your repository,
so that if the HTTP interactions change, that will show up in code review.

Next, we define a utility function that will wrap Betamax around the ``github``
:class:`~requests.Session` object at the start of the incoming HTTP request,
and unwrap it afterwards.
This allows Betamax to record and intercept HTTP requests
during the test. Note that we also use ``request.addfinalizer`` to remove
these "before_request" and "after_request" functions, so that they don't
interfere with other tests. If you are recreating your ``app`` object
from scratch each time using
:ref:`the application factory pattern <flask:app-factories>`,
you don't need to include these ``request.addfinalizer`` lines.

In the actual test, we check for the :envvar:`GITHUB_OAUTH_ACCESS_TOKEN`
environment variable. When recording a cassette with Betamax, it will
send real HTTP requests to the OAuth provider, so you'll need to include
a real OAuth access token if you expect the API call to succeed.
However, once the cassette has been recorded, you can re-run the tests
without setting this environment variable.

Also notice that you can (and should!) make assertions in your test that
expect a particular API response. In this test, I assert that the current
user is named ``@singingwolfboy``. I can do that, because when I recorded
the cassette, that was the GitHub user that I used. When the cassette is
replayed in the future, the API response will always be the same, so
I can write my assertions expecting that.

Provided Pytest Fixture
-----------------------

.. automodule:: flask_dance.fixtures.pytest

.. _pytest: https://docs.pytest.org/
.. _Betamax: https://github.com/betamaxpy/betamax
.. _Requests: https://requests.kennethreitz.org/
.. _@sigmavirus24: https://github.com/sigmavirus24/
