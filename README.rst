Flask-Dance |build-status| |coverage-status| |docs|
===================================================
Doing the OAuth dance with style using Flask, requests, and oauthlib. Currently,
only OAuth consumers are supported, but this project could easily support
OAuth providers in the future, as well. The `full documentation for this project
is hosted on ReadTheDocs <http://flask-dance.readthedocs.io/>`_,
including the full list of `supported OAuth providers`_,
but this README will give you a taste of the features.

Installation
============

Just the basics:

.. code-block:: bash

    $ pip install Flask-Dance

Or if you're planning on using the `SQLAlchemy`_ storage:

.. code-block:: bash

    $ pip install Flask-Dance[sqla]

Quickstart
==========
If you want your users to be able to log in to your app from any of the
`supported OAuth providers`_, you've got it easy. Here's an example using GitHub:

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

If you're itching to try it out, check out the `flask-dance-github`_ example
repository, with detailed instructions for how to run this code.

The ``github`` object is a `context local`_, just like ``flask.request``. That means
that you can import it in any Python file you want, and use it in the context
of an incoming HTTP request. If you've split your Flask app up into multiple
different files, feel free to import this object in any of your files, and use
it just like you would use the ``requests`` module.

You can also use Flask-Dance with any OAuth provider you'd like, not just the
pre-set configurations. `See the documentation for how to use other OAuth
providers. <http://flask-dance.readthedocs.io/en/latest/providers.html>`_

.. _flask-dance-github: https://github.com/singingwolfboy/flask-dance-github
.. _context local: http://flask.pocoo.org/docs/latest/quickstart/#context-locals

Storages
========
By default, OAuth access tokens are stored in Flask's session object.
This means that if the user ever clears their browser cookies, they will
have to go through the OAuth dance again, which is not good.
You're better off storing access tokens
in a database or some other persistent store, and Flask-Dance has support for
swapping out the token storage. For example, if you're using `SQLAlchemy`_,
set it up like this:

.. code-block:: python

    from flask_sqlalchemy import SQLAlchemy
    from flask_dance.consumer.storage.sqla import OAuthConsumerMixin, SQLAlchemyStorage

    db = SQLAlchemy()

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        # ... other columns as needed

    class OAuth(OAuthConsumerMixin, db.Model):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    # get_current_user() is a function that returns the current logged in user
    blueprint.storage = SQLAlchemyStorage(OAuth, db.session, user=get_current_user)

The SQLAlchemy storage seamlessly integrates with `Flask-SQLAlchemy`_,
as well as `Flask-Login`_ for user management, and `Flask-Caching`_ for caching.

Full Documentation
==================
This README provides just a taste of what Flask-Dance is capable of. To see more,
`read the documentation on ReadTheDocs <http://flask-dance.readthedocs.io/>`_.

.. _supported OAuth providers: https://flask-dance.readthedocs.io/en/latest/providers.html
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Flask-SQLAlchemy: http://pythonhosted.org/Flask-SQLAlchemy/
.. _Flask-Login: https://flask-login.readthedocs.io/
.. _Flask-Caching: https://flask-caching.readthedocs.io/

.. |build-status| image:: https://github.com/singingwolfboy/flask-dance/workflows/Test/badge.svg
   :target: https://github.com/singingwolfboy/flask-dance/actions?query=workflow%3ATest
   :alt: Build status
.. |coverage-status| image:: http://codecov.io/github/singingwolfboy/flask-dance/coverage.svg?branch=main
   :target: http://codecov.io/github/singingwolfboy/flask-dance?branch=main
   :alt: Test coverage
.. |docs| image:: https://readthedocs.org/projects/flask-dance/badge/?version=latest&style=flat
   :target: http://flask-dance.readthedocs.io/
   :alt: Documentation
