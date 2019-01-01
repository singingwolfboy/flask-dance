Twitter Quickstart
==================

Set up the application
----------------------
Go to Twitter Application Manager at https://apps.twitter.com and create a
new app. The application's "Callback URL" must be
``http://127.0.0.1:5000/login/twitter/authorized``. The domain ``localhost`` will not work with Twitter!
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

    @app.route("/twitter/login")
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

If you run this code locally or without HTTPS enabled (see warning below), you
must set the :envvar:`OAUTHLIB_INSECURE_TRANSPORT` environment variable to
to disable the HTTPS requirement imposed by ``oauthlib``, which is part of Flask-Dance. For example, if
you put this code in a file named ``twitter.py`` on your machine, you could
run:

.. code-block:: bash

    $ export OAUTHLIB_INSECURE_TRANSPORT=1
    $ python twitter.py

Visit ``http://127.0.0.1:5000`` in your browser, and you should start the OAuth dance
immediately after you click on the Signin with Twitter hyperlink.

In your view, make sure you use a plain hyperlink to begin the dance
so that the redirect loads Twitter's confirmation page in the browser.

.. code-block:: HTML

    <a href="/twitter/login">Sign in with Twitter</a>

You can only use http libraries like axios to check the
authentication status.

For instance, when the component mounts, you can call a function to check
the authentication status. If the authentication fails, then
you can display a hyperlink for the user to begin the dance, or
if it succeeds, then simply display the authenticated username.

The following example uses axios and vuejs but this could be ported to
react, angular, or vanila javascript. You could create 3 state variables:
welcome (String ""), authenticated (Boolean false),
authenticateCheckComplete (Boolean false), and then use these to
either show the hyperlink or the authenticated username.

.. code-block:: javascript

    function checkAuthentication(){
        const self = this;

        const url = (document.domain === "127.0.0.1")
            ? 'http://127.0.0.1:5000/twitter/auth' : 'https://your-production-domain/twitter/auth'

        axios.get(url).then(
            response => {
                if (response.data.screen_name) {
                    self.welcome = "welcome " + response.data.screen_name;
                    self.authenticated = true;
                }
            }
        ).catch(error => {
            this.errored = error
        }).finally(() => self.authenticateCheckComplete = true);

    }


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
