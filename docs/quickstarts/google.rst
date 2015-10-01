Google Quickstart
=================

Setup Application
-----------------
Visit the Google Developers Console at https://console.developers.google.com
and create a new project. In the "APIs & auth" section, click on "Credentials",
and then click the "Create a new Client ID" button. Select "Web Application"
for the application type, and click the "Configure consent screen" button.
Put in your application information, and click Save. Once you've done that,
you'll see two new fields: "Authorized JavaScript origins" and
"Authorized redirect URIs". Put ``http://localhost:5000/login/google/authorized``
into "Authorized redirect URIs", and click "Create Client ID".
Take note of the "Client ID" and "Client Secret" for the application.
As a final step, in the "APIs" section, enable the "Google+ API".

Code
----
.. code-block:: python

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.google import make_google_blueprint, google

    app = Flask(__name__)
    app.secret_key = "supersekrit"
    blueprint = make_google_blueprint(
        client_id="my-key-here",
        client_secret="my-secret-here",
        scope=["profile", "email"]
    )
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        if not google.authorized:
            return redirect(url_for("google.login"))
        resp = google.get("/plus/v1/people/me")
        assert resp.ok, resp.text
        return "You are {email} on Google".format(email=resp.json()["emails"][0]["value"])

    if __name__ == "__main__":
        app.run()

.. note::
    You must replace ``my-key-here`` and ``my-secret-here`` with the client ID
    and client secret that you got from your Google application.

.. note::
    If you are running this code on Heroku, you'll need to use the
    :class:`werkzeug.contrib.fixers.ProxyFix` middleware. See :doc:`../proxies`.

When you run this code locally, you must set the
:envvar:`OAUTHLIB_INSECURE_TRANSPORT` environment variable for it to work.
You also must set the :envvar:`OAUTHLIB_RELAX_TOKEN_SCOPE` environment variable
to account for Google changing the requested OAuth scopes on you.
For example, if you put this code in a file named ``google.py``, you could run:

.. code-block:: bash

    $ export OAUTHLIB_INSECURE_TRANSPORT=1
    $ export OAUTHLIB_RELAX_TOKEN_SCOPE=1
    $ python google.py

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
blueprint has two views: ``/google``, which is the view that the user visits
to begin the OAuth dance, and ``/google/authorized``, which is the view that
the user is redirected to at the end of the OAuth dance. Because we set the
``url_prefix`` to be ``/login``, the end result is that the views are at
``/login/google`` and ``/login/google/authorized``. The second view is the
"authorized redirect URI" that you must tell Google about when you create
the application.

The ``google`` variable is a :class:`requests.Session` instance, which will be
be preloaded with the user's access token once the user has gone through the
OAuth dance. You can check the ``google.authorized`` boolean to determine if
the access token is loaded. Whether the access token is loaded or not,
you can use all the normal ``requests`` methods, like
:meth:`~requests.Session.get` and :meth:`~requests.Session.post`,
to make HTTP requests. If you only specify the path component of the URL,
the domain will default to ``https://www.googleapis.com``.
