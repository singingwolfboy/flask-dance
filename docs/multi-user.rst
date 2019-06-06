Multi-User Setups
=================

Many websites are designed to have multiple user accounts, where each user has
one or more OAuth connections to other websites, like Google or Twitter.
This is a perfectly valid use-case for OAuth, but in order to implement it
correctly, you need to think carefully about how these OAuth connections are
created and used. There are a lot of unexpected edge-cases
that can take you by surprise.

Defining Expected Behavior
--------------------------

User Association vs User Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Are users expected to create an account on your website *first*, and then
associate OAuth connections *afterwards*? Or does logging in with an an OAuth
provider *create an account* for the user on your site automatically?

The first option (user association) is useful when you expect users to
primarily log in to your website using a username/password combination,
but want to allow your users to perform actions on other sites via OAuth.
For example, maybe you want to build your own social network website,
and allow users to invite their friends from Facebook and their followers
on Twitter. Typically, this setup means that users are able to associate
their accounts with other websites via OAuth, but they are not required to
do so.

The second option (user creation) is useful when you expect users to
primarily (or exclusively) log in to your website using an OAuth connection.
For example, maybe you don't want your users to have to remember another
username/password combination, so instead, you have a "Log In with Google"
or "Log In with GitHub" button on your website. When a user clicks on that
button and logs in with the respective service, they automatically create an
account on your website in the process. Typically, this setup means that users
cannot create an account on your website without associating it with an
OAuth connection.

Associations with Multiple Providers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Can a user associate one account with multiple different OAuth providers?
For example, can a user login with Google *or* login with GitHub, and log into
the same account whichever option they pick?

This is particularly complicated if you've chosen user creation via OAuth,
instead of user association. When a user logs in with a provider, and your
website hasn't seen that particular user on that particular provider before,
how does your website know whether to create a new user on your website, or
link this provider to an existing user on your website? If you use user
association, you can simply require that the user should already be logged
in to their local account before they can associate that local account
with an OAuth provider. But if you use user creation, that requirement is
almost impossible to enforce, because typically people don't understand
that they *have* a local user account.

Flask-Dance's Default Behavior
------------------------------

Flask-Dance does the best it can to resolve these issues for you, while
allowing you to take control in complex circumstances. Different token storages
may handle this differently, but for simplicity, this document will
refer to the :ref:`SQLAlchemy storage <sqlalchemy-storage>`.

User Association vs User Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Flask-Dance will *never* create user accounts for your users automatically.
Flask-Dance *only* handles creating OAuth associations and retrieving them
on a per-user basis. By default, Flask-Dance will associate new OAuth
connections with the local user that is currently logged in.

What happens if there no local user is currently logged in? That depends
on the ``user_required`` parameter of the
:class:`~flask_dance.consumer.storage.sqla.SQLAlchemyStorage` class. If it is
``False``, Flask-Dance will create an association that isn't linked to
any particular user in your application.
This is handy if you don't actually *have* local user accounts in your
application, and are using Flask-Dance to connect your entire website to one
single remote user. For example, this could be the desired behavior if your
website is actually a bot that responds to incoming requests by making API
calls to a third-party website, like a Twitter bot that tweets in response
to certain HTTP requests.

If the ``user_required`` parameter is set to ``True``, and no local user is
currently logged in, then Flask-Dance will raise an exception when trying to
associate an OAuth connection with the local user. The only way to correctly
resolve this situation is to override Flask-Dance's default behavior and
specify exactly how to create a local user.

Associations with Multiple Providers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, Flask-Dance will happily associate multiple different
OAuth providers with a single user account. This is why the ``OAuth`` model
in SQLAlchemy must be separate from the ``User`` model: so that you can
associate multiple different ``OAuth`` models with a single ``User`` model.

Since Flask-Dance does user association by default, rather than user creation,
you don't need to worry about the question of how Flask-Dance will handle
new OAuth associations. Using the default behavior, Flask-Dance will *never*
create a new user for the connection; instead, it will *always* associate
the connection with an existing user.

Overriding the Default Behavior
-------------------------------

If you want to allow users to log in with OAuth, and create local user accounts
automatically when they do so, you'll need to override Flask-Dance's default
behavior. To do so, you'll need to hook into the
:data:`~flask_dance.consumer.oauth_authorized` signal.

Flask-Dance's default behavior comes from storing the OAuth token for you
automatically. To override the default behavior, write a function that
subscribes to this signal, handles it the way *you* want,
and returns ``False`` or a :class:`~werkzeug.wrappers.Response` object.
Returning ``False`` or a :class:`~werkzeug.wrappers.Response` object
from this signal handler indicates to Flask-Dance that it should not
try to store the OAuth token for you. For example, returning a custom redirect
like :func:`flask.redirect` would override the default behavior.

.. warning::

    If you return ``False`` from a
    :data:`~flask_dance.consumer.oauth_authorized` signal handler,
    and you do *not* store the OAuth token in your database,
    the OAuth token will be lost, and you will not be able to use it to make
    API calls in the future!

Here's an example of how you might want to override Flask-Dance's default
behavior in order to create user accounts automatically:

.. code-block:: python

    import flask
    from flask import flash
    from flask_security import current_user, login_user
    from flask_dance.consumer import oauth_authorized
    from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
    from flask_dance.contrib.github import make_github_blueprint
    from sqlalchemy.orm.exc import NoResultFound
    from myapp.models import db, OAuth, User


    github_bp = make_github_blueprint(
        storage=SQLAlchemyStorage(OAuth, db.session, user=current_user)
    )


    # create/login local user on successful OAuth login
    @oauth_authorized.connect_via(github_bp)
    def github_logged_in(blueprint, token):
        if not token:
            flash("Failed to log in with GitHub.", category="error")
            return False

        resp = blueprint.session.get("/user")
        if not resp.ok:
            msg = "Failed to fetch user info from GitHub."
            flash(msg, category="error")
            return False

        github_info = resp.json()
        github_user_id = str(github_info["id"])

        # Find this OAuth token in the database, or create it
        query = OAuth.query.filter_by(
            provider=blueprint.name,
            provider_user_id=github_user_id,
        )
        try:
            oauth = query.one()
        except NoResultFound:
            oauth = OAuth(
                provider=blueprint.name,
                provider_user_id=github_user_id,
                token=token,
            )

        if oauth.user:
            # If this OAuth token already has an associated local account,
            # log in that local user account.
            # Note that if we just created this OAuth token, then it can't
            # have an associated local account yet.
            login_user(oauth.user)
            flash("Successfully signed in with GitHub.")

        else:
            # If this OAuth token doesn't have an associated local account,
            # create a new local user account for this user. We can log
            # in that account as well, while we're at it.
            user = User(
                # Remember that `email` can be None, if the user declines
                # to publish their email address on GitHub!
                email=github_info["email"],
                name=github_info["name"],
            )
            # Associate the new local user account with the OAuth token
            oauth.user = user
            # Save and commit our database models
            db.session.add_all([user, oauth])
            db.session.commit()
            # Log in the new local user account
            login_user(user)
            flash("Successfully signed in with GitHub.")

        # Since we're manually creating the OAuth model in the database,
        # we should return False so that Flask-Dance knows that
        # it doesn't have to do it. If we don't return False, the OAuth token
        # could be saved twice, or Flask-Dance could throw an error when
        # trying to incorrectly save it for us.
        return False

This example code does not include implementations for the ``User``
and ``OAuth`` models: you can see that these models are imported from another
file. However, notice that the ``OAuth`` model has a field called
``provider_user_id``, which is used to store the user ID of the GitHub user.
The example code uses that ID to check if we've already saved an OAuth token
in the database for this GitHub user.
