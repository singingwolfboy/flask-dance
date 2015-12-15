Slack Quickstart
================

Setup Application
-----------------
Visit https://api.slack.com/applications/new
to register an application on Slack. The application's "Redirect URI(s)"
must contain ``http://localhost:5000/login/slack/authorized``.
Take note of the "Client ID" and "Client Secret" for the application.

Code
----
.. code-block:: python

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.slack import make_slack_blueprint, slack

    app = Flask(__name__)
    app.secret_key = "supersekrit"
    blueprint = make_slack_blueprint(
        client_id="my-key-here",
        client_secret="my-secret-here",
        scope=["identify", "chat:write:bot"],
    )
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        if not slack.authorized:
            return redirect(url_for("slack.login"))
        resp = slack.post("chat.postMessage", data={
            "channel": "#general",
            "text": "Hello, world!",
            "icon_emoji": ":robot_face:",
        })
        assert resp.json()["ok"], resp.text
        return 'I just said "Hello, world!" in the #general channel!'

    if __name__ == "__main__":
        app.run()

.. note::
    You must replace ``my-key-here`` and ``my-secret-here`` with the client ID
    and client secret that you got from your Slack application.

.. note::
    If you are running this code on Heroku, you'll need to use the
    :class:`werkzeug.contrib.fixers.ProxyFix` middleware. See :doc:`../proxies`.

When you run this code locally, you must set the
:envvar:`OAUTHLIB_INSECURE_TRANSPORT` environment variable for it to work.
You also must set the :envvar:`OAUTHLIB_RELAX_TOKEN_SCOPE` environment variable
to account for Slack changing the requested OAuth scopes on you.
For example, if you put this code in a file named ``slack.py``, you could run:

.. code-block:: bash

    $ export OAUTHLIB_INSECURE_TRANSPORT=1
    $ export OAUTHLIB_RELAX_TOKEN_SCOPE=1
    $ python slack.py

Visit `localhost:5000`_ in your browser, and you should start the OAuth dance
immediately.

.. _localhost:5000: http://localhost:5000/

.. warning::
    Do *NOT* set :envvar:`OAUTHLIB_INSECURE_TRANSPORT` in production. Setting
    this variable allows you to use insecure ``http`` for OAuth communication.
    However, for security, all OAuth interactions must occur over secure
    ``https`` when running in production.

    However, you can (and probably should) set
    :envvar:`OAUTHLIB_RELAX_TOKEN_SCOPE` when running in production.

Explanation
-----------
This code makes a :ref:`blueprint <flask:blueprints>` that implements the views
necessary to be a consumer in the :doc:`OAuth dance <../how-oauth-works>`. The
blueprint has two views: ``/slack``, which is the view that the user visits
to begin the OAuth dance, and ``/slack/authorized``, which is the view that
the user is redirected to at the end of the OAuth dance. Because we set the
``url_prefix`` to be ``/login``, the end result is that the views are at
``/login/slack`` and ``/login/slack/authorized``. The second view is the
"Redirect URI" that you must tell Slack about when you create
the application.

The ``slack`` variable is a :class:`requests.Session` instance, which will be
be preloaded with the user's access token once the user has gone through the
OAuth dance. You can check the ``slack.authorized`` boolean to determine if
the access token is loaded. Whether the access token is loaded or not,
you can use all the normal ``requests`` methods, like
:meth:`~requests.Session.get` and :meth:`~requests.Session.post`,
to make HTTP requests. If you only specify the Slack method name you want
to call, the rest of the URL will be filled in for you. For example, if
you want to make a request to ``https://slack.com/api/auth.test``, you
can simply refer to ``auth.test``.
