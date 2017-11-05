Nylas Quickstart
================

Set up the application
-----------------
Visit https://developer.nylas.com/ to sign up for a Nylas Developer account.
On the Nylas Developer dashboard, click on the "Settings" button, and in the
"Callbacks" tab, add ``http://localhost:5000/login/nylas/authorized`` as
a callback URL.
Take note of the API ID and API Secret displayed on the dashboard.

Code
----
.. code-block:: python

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.nylas import make_nylas_blueprint, nylas

    app = Flask(__name__)
    app.secret_key = "supersekrit"
    nylas_bp = make_nylas_blueprint(
        app_id="my-app-id-here",
        app_secret="my-app-secret-here",
    )
    app.register_blueprint(nylas_bp, url_prefix="/login")

    @app.route("/")
    def index():
        if not nylas.authorized:
            return redirect(url_for("nylas.login"))
        resp = nylas.get("/account")
        assert resp.ok
        return "You are {name} on Nylas".format(name=resp.json()["name"])

    if __name__ == "__main__":
        app.run()


.. note::
    You must replace ``my-key-here`` and ``my-secret-here`` with the API ID
    and API Secret that you got from the Nylas Developer dashboard.

.. note::
    If you are running this code on Heroku, you'll need to use the
    :class:`werkzeug.contrib.fixers.ProxyFix` middleware. See :doc:`../proxies`.

When you run this code, you must set the :envvar:`OAUTHLIB_INSECURE_TRANSPORT`
environment variable for it to work. For example, if you put this code in a
file named ``nylas.py``, you could run:

.. code-block:: bash

    $ export OAUTHLIB_INSECURE_TRANSPORT=1
    $ python nylas.py

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
blueprint has two views: ``/nylas``, which is the view that the user visits
to begin the OAuth dance, and ``/nylas/authorized``, which is the view that
the user is redirected to at the end of the OAuth dance. Because we set the
``url_prefix`` to be ``/login``, the end result is that the views are at
``/login/nylas`` and ``/login/nylas/authorized``. The second view is the
callback URL that you must tell Nylas about when you create your developer
account.

The ``nylas`` variable is a :class:`requests.Session` instance, which will be
be preloaded with the user's access token once the user has gone through the
OAuth dance. You can check the ``nylas.authorized`` boolean to determine if
the access token is loaded. Whether the access token is loaded or not,
you can use all the normal ``requests`` methods, like
:meth:`~requests.Session.get` and :meth:`~requests.Session.post`,
to make HTTP requests. If you only specify the path component of the URL,
the domain will default to ``https://api.nylas.com/``.
