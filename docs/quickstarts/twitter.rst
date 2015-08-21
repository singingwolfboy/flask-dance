Twitter Quickstart
==================

Setup Application
-----------------
Go to Twitter Application Manager at https://apps.twitter.com and create a
new app. The application's "Callback URL" must be
``http://localhost:5000/login/twitter/authorized``.
Take note of the "API Key" and "API Secret" for the application.


Code
----
.. code-block:: python

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.twitter import make_twitter_blueprint, twitter

    app = Flask(__name__)
    app.secret_key = "supersekrit"
    blueprint = make_twitter_blueprint(
        api_key="my-key-here",
        api_secret="my-secret-here",
    )
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        if not twitter.authorized:
            return redirect(url_for("twitter.login"))
        resp = twitter.get("account/settings.json")
        assert resp.ok
        return "You are @{screen_name} on Twitter".format(screen_name=resp.json()["screen_name"])

    if __name__ == "__main__":
        app.run()

.. note::
    You must replace ``my-key-here`` and ``my-secret-here`` with the API key
    and API secret that you got from your Twitter application.

.. note::
    If you are running this code on Heroku, you'll need to use the
    :class:`werkzeug.contrib.fixers.ProxyFix` middleware. See :doc:`../proxies`.

When you run this code locally, you must set the
:envvar:`OAUTHLIB_INSECURE_TRANSPORT` environment variable for it to work.
For example, if you put this code in a file named ``twitter.py``, you could run:

.. code-block:: bash

    $ export OAUTHLIB_INSECURE_TRANSPORT=1
    $ python twitter.py

Visit `localhost:5000`_ in your browser, and you should start the OAuth dance
immediately.

.. _localhost:5000: http://localhost:5000/

.. warning::
    Do *NOT* set :envvar:`OAUTHLIB_INSECURE_TRANSPORT` in production. Setting
    this variable allows you to use insecure ``http`` for OAuth communication.
    However, for security, all OAuth interactions must occur over secure
    ``https`` when running in production.

Explanation
-----------
This code makes a :ref:`blueprint <flask:blueprints>` that implements the views
necessary to be a consumer in the :doc:`OAuth dance <../how-oauth-works>`. The
blueprint has two views: ``/twitter``, which is the view that the user visits
to begin the OAuth dance, and ``/twitter/authorized``, which is the view that
the user is redirected to at the end of the OAuth dance. Because we set the
``url_prefix`` to be ``/login``, the end result is that the views are at
``/login/twitter`` and ``/login/twitter/authorized``. The second view is the
"Callback URL" that you must tell Twitter about when you create
the application.

The ``twitter`` variable is a :class:`requests.Session` instance, which will be
be preloaded with the user's access token once the user has gone through the
OAuth dance. You can check the ``twitter.authorized`` boolean to determine if
the access token is loaded. Whether the access token is loaded or not,
you can use all the normal ``requests`` methods, like
:meth:`~requests.Session.get` and :meth:`~requests.Session.post`,
to make HTTP requests. If you only specify the path component of the URL,
the domain will default to ``https://www.googleapis.com``.
