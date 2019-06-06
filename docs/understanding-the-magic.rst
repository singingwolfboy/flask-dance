Understanding the Magic
=======================

.. currentmodule:: flask_dance.consumer

Flask-Dance might initially seem like magic ("it just works!"),
but it's just code. It's complicated, but understandable. This page
will teach you how Flask-Dance works.

Making the Blueprint
--------------------

The first thing you do with Flask-Dance is make a blueprint. This is
an instance of
:class:`OAuth1ConsumerBlueprint` or :class:`OAuth2ConsumerBlueprint`,
depending on if you're using OAuth 1 or OAuth 2. (Most providers use
OAuth 2.)

When you make your blueprint, you can either pass your client ID
and client secret to the blueprint directly, or teach your blueprint
where to find those values on its own using the
:attr:`~OAuth2ConsumerBlueprint.from_config` dictionary. Using this
dictionary is usually a good idea, since it allows you to specify
these values in your application configuration instead of in
your code.

After you've made the blueprint, you need to register it on your
Flask application, just like you would with any other blueprint.

Using the Requests Session
--------------------------

The Flask-Dance blueprints have a :attr:`~OAuth2ConsumerBlueprint.session`
attribute. When you access this attribute, the blueprint
will create and return a :class:`requests.Session` object,
properly configured for OAuth authentication. You can use this object
in exactly the same way as you would normally use the Requests
library for making HTTP requests.

The pre-set configurations also allow you to import special objects
that refer to these Requests session objects. For example,
if you run this code:

.. code-block:: python

    from flask_dance.contrib.github import github

You can then call ``github.get()`` just like you do with Requests.
However, this ``github`` object is not actually a Requests session --
it's something called a :class:`~werkzeug.local.LocalProxy`.
This allows you to access the session within the context of an incoming
HTTP request, but it will *not* allow you access it outside that
context.

Checking Authorization
----------------------

When your application starts up, Flask-Dance will check your token
storage to see if there is an OAuth token already saved
there. If so, the ``authorized`` property on your Requests
Session object will be ``True``; if not, it will be ``False``.
You can use this to determine if the user needs to go through the
OAuth dance or not.

.. warning::

    If the OAuth token is expired or invalid, it will not work.
    However, this ``authorized`` property can not check this for
    you! It only checks if the token *exists*.

Starting the Dance
------------------

In order to start the OAuth dance, redirect the user to the
:meth:`~OAuth2ConsumerBlueprint.login` view from your blueprint.
You will need to provide the name of your blueprint when calling
Flask's :func:`~flask.url_for` function. For example, for the
GitHub contrib:

.. code-block:: python

    from flask import redirect, url_for

    def my_view_func():
        # ... implement whatever logic you want here
        return redirect(url_for("github.login"))

State & Security
~~~~~~~~~~~~~~~~

One of the key features of :attr:`OAuth2ConsumerBlueprint.session` is that
the requests it generates use a ``state`` variable to ensure that the source
of OAuth authorization callbacks is in fact your intended OAuth provider.
By default, the state is a random 30-character string, as provided by
:func:`oauthlib.common.generate_token`. This protects your app against one
kind of CSRF attack. For more information, see `section 10.12 of the
OAuth 2 spec <https://tools.ietf.org/html/rfc6749#section-10.12>`_.

Finishing the Dance
-------------------

After the user finishes the OAuth dance, they will be redirected
back to the :meth:`~OAuth2ConsumerBlueprint.authorized` view
from your blueprint. This will save the OAuth token to whatever
token storage you are using, and will then redirect the user
to a different page on your website.

By default, the user will be redirected back to the root page (``/``).
However, you can set the ``redirect_url`` or ``redirect_to`` arguments
in your blueprint to change this.

If you want a dynamic redirect, where the URL isn't known until
the user finishes the OAuth dance, hook into the
:data:`~flask_dance.consumer.oauth_authorized`
signal and return the redirect from your subscriber function.
For example:

.. code-block:: python

    import flask
    from flask_dance.consumer import oauth_authorized

    @oauth_authorized.connect
    def redirect_to_next_url(blueprint, token):
        # set OAuth token in the token storage backend
        blueprint.token = token
        # retrieve `next_url` from Flask's session cookie
        next_url = flask.session["next_url"]
        # redirect the user to `next_url`
        return flask.redirect(next_url)
