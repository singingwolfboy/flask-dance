.. module:: flask_dance.consumer.storage

Token Storages
==============

A Flask-Dance blueprint has a token storage associated with it,
which is an object that knows how to store and retrieve OAuth tokens
from some kind of persistent storage. A storage is most often
some kind of database, but it doesn't have to be.

.. _flask-session-storage:

Flask Session
-------------

The default token storage uses the
:ref:`Flask session <flask:sessions>` to store OAuth tokens, which is simple
and requires no configuration. However, when the user closes
their browser, their OAuth token will be lost, so its not a good choice for
production usage.

This is a great option for hobby projects, and for a "proof of concept"
to show that an idea is viable.

.. _sqlalchemy-storage:

SQLAlchemy
----------

SQLAlchemy is the "standard" ORM_ for Flask applications, and Flask-Dance
has great support for it. First, define your database model with a ``token``
column and a ``provider`` column. Flask-Dance includes a
:class:`~flask_dance.consumer.storage.sqla.OAuthConsumerMixin`
class to make this easier::

    from flask_sqlalchemy import SQLAlchemy
    from flask_dance.consumer.storage.sqla import OAuthConsumerMixin

    db = SQLAlchemy()
    class OAuth(OAuthConsumerMixin, db.Model):
        pass

Next, create an instance of the SQLAlchemy storage
and assign it to your blueprint::

    from flask_dance.consumer.storage.sqla import SQLAlchemyStorage

    blueprint.storage = SQLAlchemyStorage(OAuth, db.session)

And that's all you need -- if you don't have user accounts in your application.
If you do, it's slightly more complicated::

    from flask_sqlalchemy import SQLAlchemy
    from flask_login import current_user
    from flask_dance.consumer.storage.sqla import OAuthConsumerMixin, SQLAlchemyStorage

    db = SQLAlchemy()

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        # ... other columns as needed

    class OAuth(OAuthConsumerMixin, db.Model):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    blueprint.storage = SQLAlchemyStorage(OAuth, db.session, user=current_user)

There are two things to notice here. One, the model that you use for storing
OAuth tokens must have a :attr:`user` relationship to the user
that it is associated with.
Two, you must pass a reference to the currently logged-in user (if any)
to :class:`~flask_dance.consumer.storage.sqla.SQLAlchemyStorage`.
If you're using `Flask-Login`_, the :attr:`current_user` proxy works great,
but you could instead pass a function that returns the current
user, if you want.

You also probably want to use a caching system for your database, so that it
is more performant under heavy load. The SQLAlchemy token storage
also integrates with `Flask-Caching`_ if you pass an instance of
Flask-Caching to the storage, like this::

    from flask import Flask
    from flask_caching import Cache

    app = Flask(__name__)
    cache = Cache(app)

    # setup Flask-Dance with SQLAlchemy models...

    blueprint.storage = SQLAlchemyStorage(OAuth, db.session, cache=cache)


.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Flask-Login: https://flask-login.readthedocs.io/
.. _Flask-Caching: https://flask-caching.readthedocs.io/

Custom
------

Of course, you don't have to use `SQLAlchemy`_, you're free to use whatever
storage system you want. Writing a custom token storage is easy:
just subclass :class:`flask_dance.consumer.storage.BaseStorage` and
override the :meth:`get`, :meth:`set`, and :meth:`delete` methods.
For example, here's a storage that uses a file on disk::

    import os
    import os.path
    import json
    from flask_dance.consumer.storage import BaseStorage

    class FileStorage(BaseStorage):
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

Then, just create an instance of your storage and assign it to the
:attr:`storage` attribute of your blueprint, and Flask-Dance will use it.

.. _ORM: https://docs.python.org/3.4/howto/webservers.html#data-persistence
