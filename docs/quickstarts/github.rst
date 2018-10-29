GitHub Quickstart
=================

Set up the application
----------------------
Visit https://github.com/settings/applications/new
to register an application on GitHub. The application's "authorization
callback URL" must be ``http://localhost:5000/login/github/authorized``.
Take note of the "Client ID" and "Client Secret" for the application.

Code
----
.. code-block:: python

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.github import make_github_blueprint, github

    app = Flask(__name__)
    app.secret_key = "supersekrit"
    blueprint = make_github_blueprint(
        client_id="my-key-here",
        client_secret="my-secret-here",
    )
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        if not github.authorized:
            return redirect(url_for("github.login"))
        resp = github.get("/user")
        assert resp.ok
        return "You are @{login} on GitHub".format(login=resp.json()["login"])

    if __name__ == "__main__":
        app.run()

.. note::
    You must replace ``my-key-here`` and ``my-secret-here`` with the client ID
    and client secret that you got from your GitHub application.

.. note::
    If you are running this code on Heroku, you'll need to use the
    :class:`werkzeug.contrib.fixers.ProxyFix` middleware. See :doc:`../proxies`.

If you run this code locally or without HTTPS enabled (see warning below), you
must set the :envvar:`OAUTHLIB_INSECURE_TRANSPORT` environment variable to
to disable the HTTPS requirement imposed by ``oauthlib``, which is part of Flask-Dance. For example, if
you put this code in a file named ``github.py`` on your machine, you could
run:

.. code-block:: bash

    $ export OAUTHLIB_INSECURE_TRANSPORT=1
    $ python github.py

Visit http://localhost:5000 in your browser, and you should start the OAuth dance
immediately.

.. warning::
    :envvar:`OAUTHLIB_INSECURE_TRANSPORT` should only be used for local testing
    or over trusted connections. By default, all OAuth interactions must occur
    over secure ``https`` connections (this is enforced by ``oauthlib``). However,
    setting :envvar:`OAUTHLIB_INSECURE_TRANSPORT` disables this enforcement and
    allows OAuth to occur over insecure ``http`` connections.

Explanation
-----------
This code makes a :ref:`blueprint <flask:blueprints>` that implements the views
necessary to be a consumer in the :doc:`OAuth dance <../how-oauth-works>`. The
blueprint has two views: ``/github``, which is the view that the user visits
to begin the OAuth dance, and ``/github/authorized``, which is the view that
the user is redirected to at the end of the OAuth dance. Because we set the
``url_prefix`` to be ``/login``, the end result is that the views are at
``/login/github`` and ``/login/github/authorized``. The second view is the
"authorized callback URL" that you must tell GitHub about when you create
the application.

The ``github`` variable is a :class:`requests.Session` instance, which will be
be preloaded with the user's access token once the user has gone through the
OAuth dance. You can check the ``github.authorized`` boolean to determine if
the access token is loaded. Whether the access token is loaded or not,
you can use all the normal ``requests`` methods, like
:meth:`~requests.Session.get` and :meth:`~requests.Session.post`,
to make HTTP requests. If you only specify the path component of the URL,
the domain will default to ``https://api.github.com``.
