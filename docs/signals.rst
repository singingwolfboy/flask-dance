.. module:: flask_dance.consumer

Signals
=======

Flask-Dance supports signals, :ref:`just as Flask does <flask:signals>`.
Signals are perfect for custom processing code that you want to run at a certain
point in the OAuth dance. For example, after the dance is complete, you might
need to update the user's profile, kick off a long-running task, or simply
:ref:`flash a message <flask:message-flashing-pattern>` to let the user know
that the login was successful. It's easy, just import the appropriate signal of
the ones listed below, and connect your custom processing code to the signal.

The following signals exist in Flask-Dance:

.. data:: oauth_before_login

    .. versionadded:: 1.4.0

    This signal is sent before redirecting to the provider login page. The signal
    is sent with a ``url`` parameter specifying the redirect URL. This signal is mostly
    useful for doing things like session construction/deconstruction before the user
    is redirected.

    Example subscriber::

        import flask
        from flask_dance.consumer import oauth_before_login

        @oauth_before_login.connect
        def before_login(blueprint, url):
            flask.session["next_url"] = flask.request.args.get("next_url")

.. data:: oauth_authorized

    This signal is sent when a user completes the OAuth dance by receiving a
    response from the OAuth provider's authorize URL. The signal is invoked
    with the blueprint instance as the first argument (the *sender*), and with
    a dict of the OAuth provider's response (the *token*).

    Example subscriber::

        from flask import flash
        from flask_dance.consumer import oauth_authorized

        @oauth_authorized.connect
        def logged_in(blueprint, token):
            flash("Signed in successfully with {name}!".format(
                name=blueprint.name.capitalize()
            ))

    If you are linking OAuth records to User records, you *must* implement an
    ``@oauth_authorized`` subscriber that creates new ``User`` and ``OAuth``
    database entries for any new users, and links those two new records via
    the ``OAuth`` table's ``user_id`` field.

    If you're using OAuth 2, the user may grant you different scopes from the
    ones you requested: check the ``scope`` key in the *token* dict to
    determine what scopes were actually granted. If you don't want the *token*
    to be :doc:`stored <storages>`, simply return ``False`` from one of your
    signal receiver functions -- this can be useful if the user has declined
    to authorize your OAuth request, has granted insufficient scopes, or in some
    other way has given you a token that you don't want.

    You can also return a :class:`~flask.Response` instance from an event
    subscriber. If you do, that response will be returned to the user instead
    of the normal redirect. For example::

        from flask import redirect, url_for

        @oauth_authorized.connect
        def logged_in(blueprint, token):
            return redirect(url_for("after_oauth"))

.. data:: oauth_error

    This signal is sent when the OAuth provider indicates that there was an
    error with the OAuth dance. This can happen if your application is
    misconfigured somehow. The user will be redirected to the ``redirect_url``
    anyway, so it is your responsibility to hook into this signal and inform
    the user that there was an error.

.. _flash a message: http://flask.pocoo.org/docs/latest/patterns/flashing/
.. _blinker: http://pythonhosted.org/blinker/
