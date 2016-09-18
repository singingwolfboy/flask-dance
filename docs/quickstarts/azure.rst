Azure Quickstart
=================

Setup Application
-----------------
Visit https://apps.dev.microsoft.com/
to register an application on Azure AD. The application's "Redirect
URI" must be ``http://localhost:5000/login/azure/authorized``.
You can also follow the detailed steps described at:
https://azure.microsoft.com/en-us/documentation/articles/active-directory-v2-app-registration/
Take note of the "Application ID" (Client ID) and "Password" (Client Secret)
for the application.

Code
----
.. code-block:: python

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.azure import make_azure_blueprint, azure

    app = Flask(__name__)
    app.secret_key = "supersekrit"
    blueprint = make_azure_blueprint(
        client_id="my-key-here",
        client_secret="my-secret-here",
    )
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        if not azure.authorized:
            return redirect(url_for("azure.login"))
        resp = azure.get("/v1.0/me")
        assert resp.ok
        return "You are {mail} on Azure AD".format(mail=resp.json()["mail"])

    if __name__ == "__main__":
        app.run()

.. note::
    You must replace ``my-key-here`` and ``my-secret-here`` with the client ID
    and client secret that you got from your Azure application.

.. note::
    If you are running this code on Heroku, you'll need to use the
    :class:`werkzeug.contrib.fixers.ProxyFix` middleware. See :doc:`../proxies`.

When you run this code, you must set the :envvar:`OAUTHLIB_INSECURE_TRANSPORT`
environment variable for it to work. For example, if you put this code in a
file named ``azure.py``, you could run:

.. code-block:: bash

    $ export OAUTHLIB_INSECURE_TRANSPORT=1
    $ python azure.py

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
blueprint has two views: ``/azure``, which is the view that the user visits
to begin the OAuth dance, and ``/azure/authorized``, which is the view that
the user is redirected to at the end of the OAuth dance. Because we set the
``url_prefix`` to be ``/login``, the end result is that the views are at
``/login/azure`` and ``/login/azure/authorized``. The second view is the
"authorized callback URL" that you must tell Azure about when you create
the application.

The ``azure`` variable is a :class:`requests.Session` instance, which will be
be preloaded with the user's access token once the user has gone through the
OAuth dance. You can check the ``azure.authorized`` boolean to determine if
the access token is loaded. Whether the access token is loaded or not,
you can use all the normal ``requests`` methods, like
:meth:`~requests.Session.get` and :meth:`~requests.Session.post`,
to make HTTP requests. If you only specify the path component of the URL,
the domain will default to ``https://graph.microsoft.com``.
