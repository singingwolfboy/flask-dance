Flask-Dance |build-status| |coverage-status| |pypi| |docs|
==========================================================
Doing the OAuth dance with style using Flask, requests, and oauthlib. Currently,
only OAuth consumers are supported, but this project could easily support
OAuth providers in the future, as well. The `full documentation for this project
is hosted on ReadTheDocs <http://flask-dance.readthedocs.org/>`_, but this
README will give you a taste of the features.

Installation
============

.. code-block:: bash

    $ pip install Flask-Dance

Quickstart
==========
For `a few popular OAuth providers`_, Flask-Dance provides pre-set configurations. For
example, to authenticate with Github, just do the following:

.. code-block:: python

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.github import make_github_blueprint, github

    app = Flask(__name__)
    github_blueprint = make_github_blueprint(
        client_id="my-key-here",
        client_secret="my-secret-here",
        redirect_to="index",
    )
    app.register_blueprint(github_blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        if not github.authorized:
            return redirect(url_for("github.login"))
        resp = github.get("/user")
        assert resp.ok
        return "You are @{login} on Github".format(login=resp.json()["login"])

The ``github`` object is a `context local`_, just like ``flask.request``. That means
that you can import it in any Python file you want, and use it in the context
of an incoming HTTP request. If you've split your Flask app up into multiple
different files, feel free to import this object in any of your files, and use
it just like you would use the ``requests`` module.

You can also use Flask-Dance with other services

.. _a few popular OAuth providers: http://flask-dance.readthedocs.org/en/latest/contrib.html
.. _context local: http://flask.pocoo.org/docs/latest/quickstart/#context-locals

Custom Services
===============
Flask-Dance also allows you to build authentication blueprints for any custom OAuth
service. For these examples, we'll reimplement services in the ``contrib``
directory, but you could use whatever values you want.

.. code-block:: python

    from flask import Flask
    from flask_dance.consumer import OAuth2ConsumerBlueprint

    app = Flask(__name__)
    github_blueprint = OAuth2ConsumerBlueprint(
        "github", __name__,
        client_key="my-key-here",
        client_secret="my-secret-here",
        scope="user:email",
        base_url="https://api.github.com",
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        redirect_to="index",
    )
    app.register_blueprint(github_blueprint, url_prefix="/login")

Now, in your page template, you can do something like:

.. code-block:: jinja

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

    @github_blueprint.token_deleter
    def delete_github_token():
        user = flask.g.user
        user.github_token = None
        db.session.add(user)
        db.commit()


Signals
=======
You probably have some custom processing code that you want to run when a user
logs in. You might need to update their user profile, fire an event, or
simply `flash a message`_ to let them know they've logged in. That's a perfect
case for a signal, powered by the `blinker`_ library. Just make sure that
blinker is installed, and connect to the ``flask_dance.consumer.oauth_authorized``
signal:

.. code-block:: python

    from flask import flash
    from flask_dance.consumer import oauth_authorized

    @oauth_authorized.connect
    def github_logged_in(blueprint, token):
        if "error" in token:
            flash("You denied the request to sign in. Please try again.")
            del blueprint.token
        else:
            flash("Signed in successfully with {name}!".format(
                name=blueprint.name.capitalize()
            ))

The argument will be called with the blueprint instance as the first argument,
and the token object from the OAuth provider as a keyword argument.
Remember that OAuth errors can happen, and just because your function gets
called doesn't mean that the OAuth dance was successful: check the token object
for information from the OAuth provider to see what happened. If you're using
OAuth 2, the user may also grant you different scopes than the ones you
requested, so you should verify that, as well. By the time this function is
called, the token will already be saved, so if you want to delete the
saved token from storage, you can just delete the ``token`` property from
the blueprint. That will call your ``token_deleter`` function,
or remove it from the Flask session if you haven't defined a ``token_deleter``
function.

.. _flash a message: http://flask.pocoo.org/docs/latest/patterns/flashing/
.. _blinker: http://pythonhosted.org/blinker/

.. |build-status| image:: https://travis-ci.org/singingwolfboy/flask-dance.svg?branch=master
   :target: https://travis-ci.org/singingwolfboy/flask-dance
   :alt: Build status
.. |coverage-status| image:: https://img.shields.io/coveralls/singingwolfboy/flask-dance.svg
   :target: https://coveralls.io/r/singingwolfboy/flask-dance?branch=master
   :alt: Test coverage
.. |pypi| image:: https://pypip.in/version/Flask-Dance/badge.svg
   :target: https://pypi.python.org/pypi/Flask-Dance/
   :alt: Latest Version
.. |docs| image:: https://readthedocs.org/projects/flask-dance/badge/?version=latest
   :target: http://flask-dance.readthedocs.org/
   :alt: Documentation
