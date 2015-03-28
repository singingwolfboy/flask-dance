.. module:: flask_dance.consumer.storage

Token Storage Backends
======================
A Flask-Dance blueprint has a "storage backend" associated with it, which is
simply an object that knows how to store and retrieve OAuth tokens. The storage
backend can access the blueprint, so that it can use the request context
(logged in user, etc) to determine *which* token needs to be retrieved.
The default storage backend uses the :ref:`Flask session <flask:sessions>`,
which is simple and requires no configuration. However, when the user closes
their browser, the OAuth token will be lost, so its not a good choice for
production usage. Fortunately, Flask-Dance comes with some other options for
storage backends.

.. _sqlalchemy-token-storage-backend:

SQLAlchemy
----------

SQLAlchemy is the "standard" database for Flask applications, and Flask-Dance
has great support for it. First, define your database model with a ``token``
column and a ``provider`` column. Flask-Dance includes a
:class:`~flask_dance.consumer.storage.sqla.OAuthConsumerMixin` class to make this easier::

    from flask_sqlalchemy import SQLAlchemy
    from flask_dance.consumer.storage.sqla import OAuthConsumerMixin

    db = SQLAlchemy()
    class OAuth(db.Model, OAuthConsumerMixin):
        pass

Next, create an instance of the SQLAlchemy token storage backend and assign
it to your blueprint::

    from flask_dance.consumer.storage.sqla import SQLAlchemyStorage

    storage = SQLAlchemyStorage(blueprint, OAuth, db.session)
    blueprint.token_storage = storage

And that's all you need -- if you don't have user accounts in your application.
If you do, it's slightly more complicated::

    from flask_sqlalchemy import SQLAlchemy
    from flask_login import current_user
    from flask_dance.consumer.storage.sqla import OAuthConsumerMixin, SQLAlchemyStorage

    db = SQLAlchemy()

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        # ... other columns as needed

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    storage = SQLAlchemyStorage(blueprint, OAuth, db.session, user=current_user)
    blueprint.token_storage = storage

There are two things to notice here. One, the model that you use for storing
OAuth tokens must have a `user` relationship to the user that it is associated
with. Two, you must pass a reference to the currently logged-in user (if any)
to :class:`~flask_dance.consumer.storage.sqla.SQLAlchemyStorage`.
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

    storage = SQLAlchemyStorage(blueprint, OAuth, db.session, cache=cache)
    blueprint.token_storage = storage


.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Flask-Login: https://flask-login.readthedocs.org/
.. _Flask-Cache: http://pythonhosted.org/Flask-Cache/

Custom
------
Of course, you don't have to use `SQLAlchemy`_, you're free to use whatever
storage system you want. Writing a custom token storage backend is easy:
just subclass :class:`flask_dance.consumer.storage.BaseTokenStorage` and
override the `get`, `set`, and `delete` methods. For example, here's a
backend that uses a file on disk::

    import os
    import os.path
    import json
    from flask_dance.consumer.storage import BaseTokenStorage

    class FileStorage(BaseTokenStorage):
        def __init__(self, blueprint, filepath):
            super(FileStorage, self).__init__(blueprint)
            self.filepath = filepath

        def get(self):
            if not os.path.exists(self.filepath):
                return None
            with open(self.filepath) as f:
                return json.load(f)

        def set(self, token):
            with open(self.filepath, "w") as f:
                json.dump(f)

        def delete(self):
            os.remove(self.filepath)

Then, just create an instance of your storage system and assign it to the
:attr:`token_storage` attribute of your blueprint, and Flask-Dance will use it.
