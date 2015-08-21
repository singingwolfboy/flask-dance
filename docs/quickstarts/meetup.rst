Meetup Quickstart
==================

Setup Application
-----------------
Visit the Meetup OAuth Consumer page at
https://secure.meetup.com/meetup_api/oauth_consumers/
and create a new consumer. Put in
``http://localhost:5000/login/meetup/authorized``
for the redirect URI. Agree to the terms of service, and register your
consumer to get an OAuth key and secret.

Code
----
.. code-block:: python

    from flask import Flask, redirect, url_for
    from flask_dance.contrib.meetup import make_meetup_blueprint, meetup

    app = Flask(__name__)
    app.secret_key = "supersekrit"
    blueprint = make_meetup_blueprint(
        key="my-key-here",
        secret="my-secret-here",
    )
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        if not meetup.authorized:
            return redirect(url_for("meetup.login"))
        resp = meetup.get("member/self")
        assert resp.ok
        return "You are {name} on Meetup".format(name=resp.json()["name"])

    if __name__ == "__main__":
        app.run()

.. note::
    You must replace ``my-key-here`` and ``my-secret-here`` with the client ID
    and client secret that you got from your Meetup application.

.. note::
    If you are running this code on Heroku, you'll need to use the
    :class:`werkzeug.contrib.fixers.ProxyFix` middleware. See :doc:`../proxies`.

When you run this code locally, you must set the
:envvar:`OAUTHLIB_INSECURE_TRANSPORT` environment variable for it to work.
For example, if you put this code in a file named ``meetup.py``, you could run:

.. code-block:: bash

    $ export OAUTHLIB_RELAX_TOKEN_SCOPE=1
    $ python meetup.py

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
blueprint has two views: ``/meetup``, which is the view that the user visits
to begin the OAuth dance, and ``/meetup/authorized``, which is the view that
the user is redirected to at the end of the OAuth dance. Because we set the
``url_prefix`` to be ``/login``, the end result is that the views are at
``/login/meetup`` and ``/login/meetup/authorized``. The second view is the
"redirect URI" that you must tell Meetup about when you create
the app.

The ``meetup`` variable is a :class:`requests.Session` instance, which will be
be preloaded with the user's access token once the user has gone through the
OAuth dance. You can check the ``meetup.authorized`` boolean to determine if
the access token is loaded. Whether the access token is loaded or not,
you can use all the normal ``requests`` methods, like
:meth:`~requests.Session.get` and :meth:`~requests.Session.post`,
to make HTTP requests. If you only specify the path component of the URL,
the domain will default to ``https://api.meetup.com``.
