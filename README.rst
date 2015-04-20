Flask-Dance |build-status| |coverage-status| |pypi| |docs|
==========================================================
Doing the OAuth dance with style using Flask, requests, and oauthlib. Currently,
only OAuth consumers are supported, but this project could easily support
OAuth providers in the future, as well. The `full documentation for this project
is hosted on ReadTheDocs <http://flask-dance.readthedocs.org/>`_, but this
README will give you a taste of the features.

Installation
============

Just the basics:

.. code-block:: bash

    $ pip install Flask-Dance

Or if you're planning on using the `SQLAlchemy`_ backend:

.. code-block:: bash

    $ pip install Flask-Dance[sqla]

Quickstart
==========
For `a few popular OAuth providers`_, Flask-Dance provides pre-set configurations. For
example, to authenticate with Github, just do the following:

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
        return "You are @{login} on Github".format(login=resp.json()["login"])

    if __name__ == "__main__":
        app.run()

**NOTE:** For this example to work, you must first `register an application on
Github`_ to get a ``client_id`` and ``client_secret``. The application's
authorization callback URL must be ``http://localhost:5000/login/github/authorized``.
You'll also need to set the `OAUTHLIB_INSECURE_TRANSPORT`_ environment variable,
so that oauthlib allows you to use HTTP rather than HTTPS.

.. _register an application on Github: https://github.com/settings/applications/new
.. _OAUTHLIB_INSECURE_TRANSPORT: http://oauthlib.readthedocs.org/en/latest/oauth2/security.html#envvar-OAUTHLIB_INSECURE_TRANSPORT

The ``github`` object is a `context local`_, just like ``flask.request``. That means
that you can import it in any Python file you want, and use it in the context
of an incoming HTTP request. If you've split your Flask app up into multiple
different files, feel free to import this object in any of your files, and use
it just like you would use the ``requests`` module.

You can also use Flask-Dance with any OAuth provider you'd like, not just the
pre-set configurations. `See the documentation for how to use other OAuth
providers. <http://flask-dance.readthedocs.org/en/latest/consumers.html>`_

.. _a few popular OAuth providers: http://flask-dance.readthedocs.org/en/latest/providers.html
.. _context local: http://flask.pocoo.org/docs/latest/quickstart/#context-locals

Backends
========
By default, OAuth access tokens are stored in Flask's session object. This means
that if the user ever clears their browser cookies, they will have to go through
the OAuth dance again, which is not good. You're better off storing access tokens
in a database or some other persistent store, and Flask-Dance has support for
swapping out the storage backend. For example, if you're using `SQLAlchemy`_,
just set it up like this:

.. code-block:: python

    from flask_sqlalchemy import SQLAlchemy
    from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend

    db = SQLAlchemy()

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        # ... other columns as needed

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    # get_current_user() is a function that returns the current logged in user
    blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=get_current_user)

The SQLAlchemy backend seamlessly integrates with `Flask-SQLAlchemy`_,
as well as `Flask-Login`_ for user management, and `Flask-Cache`_ for caching.

Full Documentation
==================
This README provides just a taste of what Flask-Dance is capable of. To see
more, `read the documentation on ReadTheDocs <http://flask-dance.readthedocs.org/>`.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Flask-SQLAlchemy: http://pythonhosted.org/Flask-SQLAlchemy/
.. _Flask-Login: https://flask-login.readthedocs.org/
.. _Flask-Cache: http://pythonhosted.org/Flask-Cache/

.. |build-status| image:: https://travis-ci.org/singingwolfboy/flask-dance.svg?branch=master&style=flat
   :target: https://travis-ci.org/singingwolfboy/flask-dance
   :alt: Build status
.. |coverage-status| image:: https://img.shields.io/coveralls/singingwolfboy/flask-dance.svg?style=flat
   :target: https://coveralls.io/r/singingwolfboy/flask-dance?branch=master
   :alt: Test coverage
.. |pypi| image:: https://pypip.in/version/Flask-Dance/badge.svg?style=flat
   :target: https://pypi.python.org/pypi/Flask-Dance/
   :alt: Latest Version
.. |docs| image:: https://readthedocs.org/projects/flask-dance/badge/?version=latest&style=flat
   :target: http://flask-dance.readthedocs.org/
   :alt: Documentation
