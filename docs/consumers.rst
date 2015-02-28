Other Providers
===============
Flask-Dance allows you to build authentication blueprints for any OAuth
provider, not just the :doc:`pre-set configurations <contrib>`.
For these examples, we'll reimplement the Github provider,
but you could use whatever values you want.

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
    resp = github.get("/user")
    assert resp.ok
    print("Hi, @{login}!".format(login=resp.json()["login"]))

The :attr:`~OAuth2ConsumerBlueprint.session` object attached to the blueprint
is a :class:`requests.Session` object that is already properly configured
with your OAuth credentials. The fact that you are using OAuth is
completely transparent -- you don't even have to think about it!
