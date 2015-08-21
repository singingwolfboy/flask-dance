Dropbox Quickstart
==================

Setup Application
-----------------
Visit the Dropbox App Console at https://www.dropbox.com/developers/apps
and create a new app. Select "Dropbox API app", not "Drop-ins app". Decide
if your app can be limited to its own folder, provide an app name, and
agree to the terms of service. Once the app has been created, you need to
add at least one redirect URI under the OAuth 2 section: put in
``http://localhost:5000/login/dropbox/authorized`` and click Add.
Take note of the "App key" and "App Secret" for the application.

Code
----
.. code-block:: python

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.dropbox import make_dropbox_blueprint, dropbox

    app = Flask(__name__)
    app.secret_key = "supersekrit"
    blueprint = make_dropbox_blueprint(
        app_key="my-key-here",
        app_secret="my-secret-here",
    )
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        if not dropbox.authorized:
            return redirect(url_for("dropbox.login"))
        resp = dropbox.get("account/info")
        assert resp.ok
        return "You are {email} on Dropbox".format(email=resp.json()["email"])

    if __name__ == "__main__":
        app.run()

.. note::
    You must replace ``my-key-here`` and ``my-secret-here`` with the client ID
    and client secret that you got from your Dropbox application.

.. note::
    If you are running this code on Heroku, you'll need to use the
    :class:`werkzeug.contrib.fixers.ProxyFix` middleware. See :doc:`../proxies`.

When you run this code locally, you must set the
:envvar:`OAUTHLIB_INSECURE_TRANSPORT` environment variable for it to work.
For example, if you put this code in a file named ``dropbox.py``, you could run:

.. code-block:: bash

    $ export OAUTHLIB_RELAX_TOKEN_SCOPE=1
    $ python dropbox.py

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
blueprint has two views: ``/dropbox``, which is the view that the user visits
to begin the OAuth dance, and ``/dropbox/authorized``, which is the view that
the user is redirected to at the end of the OAuth dance. Because we set the
``url_prefix`` to be ``/login``, the end result is that the views are at
``/login/dropbox`` and ``/login/dropbox/authorized``. The second view is the
"redirect URI" that you must tell Dropbox about when you create
the app.

The ``dropbox`` variable is a :class:`requests.Session` instance, which will be
be preloaded with the user's access token once the user has gone through the
OAuth dance. You can check the ``dropbox.authorized`` boolean to determine if
the access token is loaded. Whether the access token is loaded or not,
you can use all the normal ``requests`` methods, like
:meth:`~requests.Session.get` and :meth:`~requests.Session.post`,
to make HTTP requests. If you only specify the path component of the URL,
the domain will default to ``https://api.dropbox.com``.
