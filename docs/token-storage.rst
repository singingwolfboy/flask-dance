.. module:: flask_dance.consumer

Token Storage
=============
By default, OAuth access tokens are stored in the
:ref:`Flask session <flask:sessions>`. This means that if the user ever
clears their browser cookies, they will have to go through the OAuth flow again,
which is not good. You're better off storing access tokens
in a database or some other persistent store.


SQLAlchemy
----------

.. versionadded:: 0.2

If you're using `SQLAlchemy`_, you've got a leg up: Flask-Dance has built-in
support for this common use case. First, define your model with a ``token``
column and a ``provider`` column. Flask-Dance includes a
:class:`~flask_dance.models.OAuthConsumerMixin` class to make this easier::

    from flask_sqlalchemy import SQLAlchemy
    from flask_dance.models import OAuthConsumerMixin

    db = SQLAlchemy()
    class OAuth(db.Model, OAuthConsumerMixin):
        pass

If you have a User model in your application, you can also set up a
:class:`~sqlalchemy.schema.ForeignKey` to your User model::

    from flask_sqlalchemy import SQLAlchemy
    from flask_dance.models import OAuthConsumerMixin

    db = SQLAlchemy()

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        # ... other columns as needed

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

Then just pass your OAuth model and your SQLAlchemy session to your blueprint
using the :meth:`~OAuth2ConsumerBlueprint.set_token_storage_sqlalchemy` method::

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session)

Or if you're using a User model, pass along a reference to the current user so
that Flask-Dance can associate users with OAuth tokens. `Flask-Login`_ provides
a ``current_user`` proxy that should work great::

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session, user=current_user)

And you should be all set! However, it's also highly recommended that you use
some kind of caching system, to prevent unnecessary load on your database.
Since Flask-Dance will automatically load the user's OAuth token at the start
of every request, and since those tokens rarely change, they are prime
candidates to be cached. Fortunately, Flask-Dance also integrates with
`Flask-Cache`_, which makes caching OAuth tokens trivial. Just pass the
``cache`` object along to the
:meth:`~OAuth2ConsumerBlueprint.set_token_storage_sqlalchemy` method, as well::

    from flask_cache import Cache
    cache = Cache(app)

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session, cache=cache)

And of course, it can also be combined with a User model::

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session, user=current_user, cache=cache)

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Flask-Login: https://flask-login.readthedocs.org/
.. _Flask-Cache: http://pythonhosted.org/Flask-Cache/

Custom Storage
--------------
Of course, you don't have to use `SQLAlchemy`_, you're free to use whatever
storage system you want. To use something else, just write custom
get, set, and delete functions, and attach them to the Blueprint object using the
:obj:`~OAuth2ConsumerBlueprint.token_getter`,
:obj:`~OAuth2ConsumerBlueprint.token_setter`, and
:obj:`~OAuth2ConsumerBlueprint.token_deleter` decorators::

    @blueprint.token_getter
    def get_token():
        user = get_current_user()
        return user.token

    @blueprint.token_setter
    def set_token(token):
        user = get_current_user()
        user.token = token
        user.save()

    @blueprint.token_deleter
    def delete_token():
        user = get_current_user()
        del user.token
        user.save()

Once you set those three functions, you'll be able to forget about them and just
reference :data:`~OAuth2ConsumerBlueprint.token`: the functions will be called
automatically as needed. Note that Flask-Dance does *not* handle caching
automatically, so you should integrating caching into your custom storage
functions! `Flask-Cache`_ is very useful for that.
