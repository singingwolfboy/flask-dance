.. module:: flask_dance.consumer.backend

Backends
========
A Flask-Dance blueprint has a backend associated with it, which is simply an
object that knows how to store and retrieve OAuth tokens from some kind of
persistent storage. The default storage backend uses the
:ref:`Flask session <flask:sessions>` to store OAuth tokens, which is simple
and requires no configuration. However, when the user closes
their browser, the OAuth token will be lost, so its not a good choice for
production usage. Fortunately, Flask-Dance comes with some other backends
to choose from.

.. _sqlalchemy-backend:

SQLAlchemy
----------

SQLAlchemy is the "standard" database for Flask applications, and Flask-Dance
has great support for it. First, define your database model with a ``token``
column and a ``provider`` column. Flask-Dance includes a
:class:`~flask_dance.consumer.backend.sqla.OAuthConsumerMixin` class to make this easier::

    from flask_sqlalchemy import SQLAlchemy
    from flask_dance.consumer.backend.sqla import OAuthConsumerMixin

    db = SQLAlchemy()
    class OAuth(db.Model, OAuthConsumerMixin):
        pass

Next, create an instance of the SQLAlchemy backend and assign it to your blueprint::

    from flask_dance.consumer.backend.sqla import SQLAlchemyBackend

    blueprint.backend = SQLAlchemyBackend(OAuth, db.session)

And that's all you need -- if you don't have user accounts in your application.
If you do, it's slightly more complicated::

    from flask_sqlalchemy import SQLAlchemy
    from flask_login import current_user
    from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend

    db = SQLAlchemy()

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        # ... other columns as needed

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user)

There are two things to notice here. One, the model that you use for storing
OAuth tokens must have a `user` relationship to the user that it is associated
with. Two, you must pass a reference to the currently logged-in user (if any)
to :class:`~flask_dance.consumer.backend.sqla.SQLAlchemyStorage`.
If you're using `Flask-Login`_, the :attr:`current_user` proxy works great,
but you could instead pass a function that returns the current
user, if you want.

You also probably want to use a caching system for your database, so that it
is more performant under heavy load. The SQLAlchemy token storage backend
also integrates with `Flask-Cache`_ if you just pass an Flask-Cache instance
to the backend, like this::

    from flask import Flask
    from flask_cache import Cache

    app = Flask(__name__)
    cache = Cache(app)

    # setup Flask-Dance with SQLAlchemy models...

    blueprint.backend = SQLAlchemyBackend(OAuth, db.session, cache=cache)


.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Flask-Login: https://flask-login.readthedocs.org/
.. _Flask-Cache: http://pythonhosted.org/Flask-Cache/

Custom
------
Of course, you don't have to use `SQLAlchemy`_, you're free to use whatever
storage system you want. Writing a custom backend is easy:
just subclass :class:`flask_dance.consumer.backend.BaseBackend` and
override the `get`, `set`, and `delete` methods. For example, here's a
backend that uses a file on disk::

    import os
    import os.path
    import json
    from flask_dance.consumer.backend import BaseBackend

    class FileBackend(BaseBackend):
        def __init__(self, filepath):
            super(FileStorage, self).__init__()
            self.filepath = filepath

        def get(self, blueprint):
            if not os.path.exists(self.filepath):
                return None
            with open(self.filepath) as f:
                return json.load(f)

        def set(self, blueprint, token):
            with open(self.filepath, "w") as f:
                json.dump(token, f)

        def delete(self, blueprint):
            os.remove(self.filepath)

Then, just create an instance of your backend and assign it to the
:attr:`backend` attribute of your blueprint, and Flask-Dance will use it.
