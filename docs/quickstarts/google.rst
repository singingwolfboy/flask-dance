Google Quickstart
=================

Set up the application
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
        resp = google.get("/oauth2/v2/userinfo")
        assert resp.ok, resp.text
        return "You are {email} on Google".format(email=resp.json()["email"])

    if __name__ == "__main__":
        app.run()

.. note::
    You must replace ``my-key-here`` and ``my-secret-here`` with the client ID
    and client secret that you got from your Google application.

.. note::
    If you are running this code on Heroku, you'll need to use the
    :class:`werkzeug.contrib.fixers.ProxyFix` middleware. See :doc:`../proxies`.

If you run this code locally or without HTTPS enabled (see warning below), you
must set the :envvar:`OAUTHLIB_INSECURE_TRANSPORT` environment variable to
to disable the HTTPS requirement imposed by ``oauthlib``, which is part of Flask-Dance. For example, if
you put this code in a file named ``google.py`` on your machine, you could
run:

.. code-block:: bash

    $ export OAUTHLIB_INSECURE_TRANSPORT=1
    $ export OAUTHLIB_RELAX_TOKEN_SCOPE=1
    $ python google.py

Visit `http://localhost:5000`_ in your browser, and you should start the OAuth dance
immediately.

.. _localhost:5000: http://localhost:5000/

.. warning::
    :envvar:`OAUTHLIB_INSECURE_TRANSPORT` should only be used for local testing
    or over trusted connections. By default, all OAuth interactions must occur
    over secure ``https`` connections (this is enfored by ``oauthlib``). However,
    setting :envvar:`OAUTHLIB_INSECURE_TRANSPORT` disables this enforcement and
    allows OAuth to occur over insecure ``http`` connections.

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

Online vs offline applications
------------------------------

Google distinguishes between online and offline applications. Online applications
are applications that only act when the user is at their keyboard, say a web
application that only calls Google API's as the user is interacting with your
application. Offline applications are applications that can act on behalf of the
user while they're not at their keyboard, for example something that runs backups
on behalf of the user at a specific point in time.

The blueprint is configured by default to get an online token. This means you'll get
a token that's valid for about an hour and after that you'll need to get a new token,
by putting the user through the OAuth flow again. If instead you request an offline
token you'll also be given a refresh token that your application can use to request
a new, short lived, token without the user needing to do anything.

.. warning::

   The refresh token is only returned the first time you put a user through the OAuth
   flow. This means you need to store the refresh token in a persistent fashion in
   order to ensure your application can renew the access token. It's therefore not
   advisable to store this using Flask's regular session, which uses a cookie. Though
   the session can be marked as persistent that won't save you if the user decides
   to clear their browser cache for example.

It's tempting to just request an offline token but if your application doesn't act
on behalf of the user while they're not at their keyboard this is in bad form. Instead,
you can install an error handler in your Flask app that will automatically retrigger the
OAuth flow when the token has expired.

.. code-block:: python

    from oauthlib.oauth2.rfc6749.errors import InvalidClientIdError

    @app.errorhandler(InvalidClientIdError)
    def token_expired(_):
        """Get a fresh access token by triggering the OAuth flow.

        Since the user has already given consent this won't cause the user to
        have to interact with anything. In most cases it'll flash by without
        the user noticing anything.
        """
        session.pop('google_oauth_token')
        return redirect(url_for('index'))

You'll need to adjust the ``redirect`` call to a URL that'll trigger the OAuth flow. You
can also manually handle the error at the callsite instead, anywhere you do a ``google.get()``
call for example, by catching the exception. That would allow you to customize the behaviour.
In all cases you'll need to remove the ``google_oauth_token`` from the session and redirect
to something that'll retrigger the OAuth flow.
