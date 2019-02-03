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

Mock Backends
=============

The simplest way to write tests with Flask-Dance is to use a
mock token storage backend. This allows you to easily control
whether Flask-Dance believes the current user is authorized
with the OAuth provider or not. Flask-Dance provides two
mock token storage backends:

.. currentmodule:: flask_dance.consumer.backend

.. autoclass:: NullBackend

.. autoclass:: MemoryBackend

Let's say you are testing the following code::

    from flask import redirect, url_for
    from flask_dance.contrib.github import make_github_blueprint, github

    app = Flask(__name__)
    github_bp = make_github_blueprint()
    app.register_blueprint(github_bp, url_prefix="/login")

    @app.route("/")
    def index():
        if github.authorized:
            return redirect(url_for("github.login"))
        return "You are authorized"

You want to write tests to cover two cases: what happens when the user
is authorized with the OAuth provider, and what happens when they are not.
Here's how you could do that with `pytest`_ and the :class:`MemoryBackend`::

    from flask_dance.consumer.backend import MemoryBackend
    from myapp import app, github_bp

    def test_index_unauthorized(monkeypatch):
        backend = MemoryBackend()
        monkeypatch.setattr(github_bp, "backend", backend)

        with app.test_client() as client:
            response = client.get("/", base_url="https://example.com")

        assert response.status_code == 302
        assert response.headers["Location"] == "https://example.com/login/github"

    def test_index_authorized(monkeypatch):
        backend = MemoryBackend({"access_token": "fake-token"})
        monkeypatch.setattr(github_bp, "backend", backend)

        with app.test_client() as client:
            response = client.get("/", base_url="https://example.com")

        assert response.status_code == 200
        text = response.get_data(as_text=True)
        assert text == "You are authorized"

In this example, we're using the
`monkeypatch fixture <https://docs.pytest.org/en/latest/monkeypatch.html>`__
to set a mock backend on the Flask-Dance blueprint. This fixture will
ensure that the original backend is put back on the blueprint after the
test is finished, so that the test doesn't change the code being tested.
Then, we create a test client and access the ``index`` view.
The mock backend will control whether ``github.authorized`` is ``True``
or ``False``, and the rest of the test asserts that the result is what
we expect.

Mock API Responses
==================

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
of the Requests, `@sigmavirus24`_.

Let's say your testing the same code as before, but now the ``index``
view looks like this::

    @app.route("/")
    def index():
        if github.authorized:
            return redirect(url_for("github.login"))
        resp = github.get("/user")
        return "You are @{login} on GitHub".format(login=resp.json()["login"])

Here's how you could test this view using Betamax::

    import os
    from flask_dance.consumer.backend import MemoryBackend
    from flask_dance.contrib.github import github
    from betamax import Betamax
    from myapp import app, github_bp

    with Betamax.configure() as config:
        config.cassette_library_dir = 'cassettes'

    def setup_betamax(app, request, cassette):
        @app.before_request
        def wrap_github_with_betamax():
            recorder = Betamax(github)
            recorder.use_cassette(cassette)
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

    def test_index_authorized(monkeypatch, request):
        access_token = os.environ.get("GITHUB_OAUTH_ACCESS_TOKEN", "fake-token")
        backend = MemoryBackend({"access_token": access_token})
        monkeypatch.setattr(github_bp, "backend", backend)

        setup_betamax(app, request, "test_index_authorized")

        assert response.status_code == 200
        text = response.get_data(as_text=True)
        assert text == "You are @singingwolfboy on GitHub"

In this example, we first
:doc:`configure Betamax globally <betamax:configuring>`
so that it stores cassettes (recorded HTTP interactions) in the ``cassettes``
directory. Betamax expects you to commit these cassettes to your repository,
so that if the HTTP interactions change, that will show up in code review.

Next, we define a utility function that will wrap Betamax around the ``github``
:class:`~requests.Session` object at the start of the incoming HTTP request, and
unwrap it afterwards. This allows Betamax to record and intercept HTTP requests
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

.. _pytest: https://docs.pytest.org/
.. _Betamax: https://github.com/betamaxpy/betamax
.. _Requests: http://docs.python-requests.org
.. _@sigmavirus24: https://github.com/sigmavirus24/
