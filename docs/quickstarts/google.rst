Google Quickstart
=================

Set up the application
----------------------
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
        scope=[
            "https://www.googleapis.com/auth/plus.me",
            "https://www.googleapis.com/auth/userinfo.email",
        ]
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

.. note::
    If you set the ``hosted_domain`` argument of ``make_google_blueprint``, be aware that this only provides UI optimization
    and is not a way of restricting access to users of a single domain. See the ``make_google_blueprint``
    :ref:`documentation warning <google_hosted_domain_warning>`.

If you run this code locally or without HTTPS enabled (see warning below), you
must set the :envvar:`OAUTHLIB_INSECURE_TRANSPORT` environment variable to
to disable the HTTPS requirement imposed by ``oauthlib``, which is part of Flask-Dance. For example, if
you put this code in a file named ``google.py`` on your machine, you could
run:

.. code-block:: bash

    $ export OAUTHLIB_INSECURE_TRANSPORT=1
    $ export OAUTHLIB_RELAX_TOKEN_SCOPE=1
    $ python google.py

Visit http://localhost:5000 in your browser, and you should start the OAuth dance
immediately.

.. warning::
    :envvar:`OAUTHLIB_INSECURE_TRANSPORT` should only be used for local testing
    or over trusted connections. By default, all OAuth interactions must occur
    over secure ``https`` connections (this is enforced by ``oauthlib``). However,
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
