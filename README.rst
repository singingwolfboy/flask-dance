Flask-Dance |build-status| |coverage-status| |docs|
===================================================
Doing the OAuth dance with style using Flask, requests, and oauthlib. Currently,
only OAuth consumers are supported, but this project could easily support
OAuth providers in the future, as well. The `full documentation for this project
is hosted on ReadTheDocs <http://flask-dance.readthedocs.org/>`_, but this
README will give you a taste of the features.

Flask-Dance currently provides pre-set OAuth configurations for the following
popular websites:

* Facebook
* GitHub
* Google
* Twitter
* JIRA
* Dropbox
* Meetup
* Slack

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
If you want your users to be able to log in to your app from any of the websites
listed above, you've got it easy. Here's an example using GitHub:

.. code-block:: python

    from flask import Flask, redirect, url_for
    from werkzeug.contrib.fixers import ProxyFix
    from flask_dance.contrib.github import make_github_blueprint, github

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app)
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

If you're itching to try it out, check out the `flask-dance-github`_ example
repository, with detailed instructions for how to run this code.

The ``github`` object is a `context local`_, just like ``flask.request``. That means
that you can import it in any Python file you want, and use it in the context
of an incoming HTTP request. If you've split your Flask app up into multiple
different files, feel free to import this object in any of your files, and use
it just like you would use the ``requests`` module.

You can also use Flask-Dance with any OAuth provider you'd like, not just the
pre-set configurations. `See the documentation for how to use other OAuth
providers. <http://flask-dance.readthedocs.org/en/latest/providers.html>`_

.. _flask-dance-github: https://github.com/singingwolfboy/flask-dance-github
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
This README provides just a taste of what Flask-Dance is capable of. To see more,
`read the documentation on ReadTheDocs <http://flask-dance.readthedocs.org/>`_.

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Flask-SQLAlchemy: http://pythonhosted.org/Flask-SQLAlchemy/
.. _Flask-Login: https://flask-login.readthedocs.org/
.. _Flask-Cache: http://pythonhosted.org/Flask-Cache/

.. |build-status| image:: https://travis-ci.org/singingwolfboy/flask-dance.svg?branch=master&style=flat
   :target: https://travis-ci.org/singingwolfboy/flask-dance
   :alt: Build status
.. |coverage-status| image:: http://codecov.io/github/singingwolfboy/flask-dance/coverage.svg?branch=master
   :target: http://codecov.io/github/singingwolfboy/flask-dance?branch=master
   :alt: Test coverage
.. |docs| image:: https://readthedocs.org/projects/flask-dance/badge/?version=latest&style=flat
   :target: http://flask-dance.readthedocs.org/
   :alt: Documentation
