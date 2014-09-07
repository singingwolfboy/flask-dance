Flask-Dance
===========
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
    from flask_dance.contrib.github import github, make_github_blueprint

    app = Flask(__name__)
    github_blueprint = make_github_blueprint(
        client_id="my-key-here",
        client_secret="my-secret-here",
        scope="user:email",
    )
    app.register_blueprint(github_blueprint)

    @app.route("/test-page")
    def test_page():
        if not github.authorized:
            return redirect(url_for("github.login", next=url_for("test-page")))
        resp = github.get("/user/emails")
        assert resp.ok
        emails = [result["email"] for result in resp.json()]
        return " ".join(emails)


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
    )
    app.register_blueprint(github_blueprint)

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
    def set_github_token(response):
        user = flask.g.user
        user.github_access_token = response["access_token"]
        user.github_scopes = response["scope"]
        db.session.add(user)
        db.commit()

    @oauth_blueprint.token_getter
    def get_github_token(identifier=None):
        user = flask.g.user
        if user.github_access_token:
            return user.github_access_token
        return None

You'll notice that the ``token_getter`` function takes an optional ``identifier``
parameter. You can use this parameter to differentate among multiple tokens
that you have have. For example, Twitter allows you to get two different kinds
of authentication tokens: application-only authentication and single-user
authentication. You could then save both tokens, and specify which you want to use
by passing the ``token`` parameter to your ``requests`` method:

.. code-block:: python

    @twitter_blueprint.token_getter
    def get_twitter_token(identifier="app"):
        if identifier not in ("user", "app"):
            raise ValueError("invalid Twitter token identifier")

        if identifier == "user":
            user = flask.g.user
            if user.twitter_oauth:
                return (user.twitter_oauth, user.twitter_oauth_secret)
            else:
                return None

        if identifier == "app":
            creds = AppCredentials.query.filter(service="twitter").first()
            if creds:
                return (creds.token, creds.secret)
            else:
                return None

.. code-block:: python

    twitter = twitter_blueprint.session
    # make a request on behalf of the user
    tweet = {"status": "Tweeting from Flask-Dance"}
    resp = twitter.post("statuses/update.json", data=tweet, token="user")
    # make a request on behalf of the application
    resp = twitter.get("statuses/home_timeline.json", token="app")
