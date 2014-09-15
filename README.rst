Flask-Dance |build-status| |coverage-status|
============================================
Doing the OAuth dance with style using Flask, requests, and oauthlib. Currently,
only OAuth consumers are supported, but this project could easily support
OAuth providers in the future, as well.

Installation
============

    $ pip install Flask-Dance

Quickstart
==========
For a few popular services, Flask-Dance provides pre-set configurations. For
example, to authenticate with Github, just do the following:

.. code-block:: python

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.github import make_github_blueprint, github

    app = Flask(__name__)
    github_blueprint = make_github_blueprint(
        client_id="my-key-here",
        client_secret="my-secret-here",
        scope="user:email",
        redirect_to="index",
    )
    app.register_blueprint(github_blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        if not github.authorized:
            return redirect(url_for("github.login"))
        resp = github.get("/user/emails")
        assert resp.ok
        emails = [result["email"] for result in resp.json()]
        return " ".join(emails)

The `github` object is a `context local`_, just like ``flask.request``. That means
that you can import it in any Python file you want, and use it in the context
of an incoming HTTP request. If you've split your Flask app up into multiple
different files, feel free to import this object in any of your files, and use
it just like you would use the ``requests`` module.

.. _context local: http://flask.pocoo.org/docs/latest/quickstart/#context-locals

Custom Services
===============
Flask-Dance also allows you to build authentication blueprints for any custom OAuth
service. For these examples, we'll reimplement services in the ``contrib``
directory, but you could use whatever values you want.

.. code-block:: python

    from flask import Flask
    from flask_dance import OAuth2ConsumerBlueprint

    app = Flask(__name__)
    github_blueprint = OAuth2ConsumerBlueprint(
        "github", __name__,
        client_key="my-key-here",
        client_secret="my-secret-here",
        request_token_params={"scope": "user:email"},
        base_url="https://api.github.com",
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        redirect_to="index",
    )
    app.register_blueprint(github_blueprint, url_prefix="/login")

Now, in your page template, you can do something like:

.. code-block:: jinja2

    <a href="{{ url_for("github.login") }}">Login with Github</a>

``url_for("github.login")`` will resolve to ``/login/github`` by default,
which will kick off the OAuth dance. The application will fetch an access token
from the configured ``access_token_url``, then redirect the user to the
``authorize_token_url``. When the user authorizes with the OAuth provider,
the user will be redirected back to ``/login/github/authorized``, which
will save the OAuth tokens and redirect the user back to the home page.
Of course, all of the details of this process can be configured and overriden
to make sure that you dance the OAuth dance precisely the way *you* want.

Once you've got your OAuth credentials, making authenticated requests couldn't
be easier!

.. code-block:: python

    github = github_blueprint.session
    resp = github.get("/user/emails")
    assert resp.ok
    for result in resp.json():
        print(result["email"])

The ``session`` object attached to the blueprint is a ``requests.Session`` object
that is already properly configured with your OAuth credentials. The fact that
you are using OAuth is completely transparent -- you don't even have to think
about it!

Token Storage
=============
By default, OAuth access tokens are stored in Flask's session object. This means
that if the user ever clears their browser cookies, they will have to go through
the OAuth flow again, which is not good. You're better off storing access tokens
in a database or some other persistent store. To do that, just write custom
get and set functions, and attach them to the Blueprint object using the
``token_getter`` and ``token_setter`` decorators:

.. code-block:: python

    @github_blueprint.token_setter
    def set_github_token(token):
        user = flask.g.user
        user.github_token = token
        db.session.add(user)
        db.commit()

    @github_blueprint.token_getter
    def get_github_token():
        user = flask.g.user
        return user.github_token

.. |build-status| image:: https://travis-ci.org/singingwolfboy/flask-dance.svg?branch=master
   :target: https://travis-ci.org/singingwolfboy/flask-dance
   :alt: Build status
.. |coverage-status| image:: https://img.shields.io/coveralls/singingwolfboy/flask-dance.svg
   :target: https://coveralls.io/r/singingwolfboy/flask-dance?branch=master
   :alt: Test coverage
