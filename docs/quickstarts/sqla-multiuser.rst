SQLAlchemy Multi-User Quickstart
================================

This quickstart will help you get started with a multi-user application where
OAuth tokens are stored using the
:ref:`SQLAlchemy backend <sqlalchemy-backend>`. You should already
be familiar with setting up a single-use Flask-Dance application -- you can
consult some of the other quickstarts for that.


Code
----
Create a file called ``multi.py`` with the following contents:

.. code-block:: python

    import sys
    from flask import Flask, redirect, url_for, flash, render_template
    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy.orm.exc import NoResultFound
    from flask_dance.contrib.github import make_github_blueprint, github
    from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
    from flask_dance.consumer import oauth_authorized, oauth_error
    from flask_login import (
        LoginManager, UserMixin, current_user,
        login_required, login_user, logout_user
    )

    # setup Flask application
    app = Flask(__name__)
    app.secret_key = "supersekrit"
    blueprint = make_github_blueprint(
        client_id="my-key-here",
        client_secret="my-secret-here",
    )
    app.register_blueprint(blueprint, url_prefix="/login")

    # setup database models
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///multi.db"
    db = SQLAlchemy()

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(256), unique=True)
        # ... other columns as needed

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    # setup login manager
    login_manager = LoginManager()
    login_manager.login_view = 'github.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # setup SQLAlchemy backend
    blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user)

    # create/login local user on successful OAuth login
    @oauth_authorized.connect_via(blueprint)
    def github_logged_in(blueprint, token):
        if not token:
            flash("Failed to log in with {name}".format(name=blueprint.name))
            return
        # figure out who the user is
        resp = blueprint.session.get("/user")
        if resp.ok:
            username = resp.json()["login"]
            query = User.query.filter_by(username=username)
            try:
                user = query.one()
            except NoResultFound:
                # create a user
                user = User(username=username)
                db.session.add(user)
                db.session.commit()
            login_user(user)
            flash("Successfully signed in with GitHub")
        else:
            msg = "Failed to fetch user info from {name}".format(name=blueprint.name)
            flash(msg, category="error")

    # notify on OAuth provider error
    @oauth_error.connect_via(blueprint)
    def github_error(blueprint, error, error_description=None, error_uri=None):
        msg = (
            "OAuth error from {name}! "
            "error={error} description={description} uri={uri}"
        ).format(
            name=blueprint.name,
            error=error,
            description=error_description,
            uri=error_uri,
        )
        flash(msg, category="error")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have logged out")
        return redirect(url_for("index"))

    @app.route("/")
    def index():
        return render_template("home.html")

    # hook up extensions to app
    db.init_app(app)
    login_manager.init_app(app)

    if __name__ == "__main__":
        if "--setup" in sys.argv:
            with app.app_context():
                db.create_all()
                db.session.commit()
                print("Database tables created")
        else:
            app.run(debug=True)

Make a ``templates`` directory next to ``multi.py``. In that directory, create
a file called ``home.html`` with the following contents:

.. code-block:: jinja

    <!DOCTYPE html>
    <head>
        <title>Flask-Dance Multi-User SQLAlchemy</title>
    </head>
    <body>
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul class="flash">
        {% for category, message in messages %}
          <li class="{{ category }}">{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    {% if current_user.is_authenticated %}
      You are logged in as {{ current_user.username }}!
      <a href="{{ url_for("logout") }}">Log out</a>
    {% else %}
      You are not logged in.
      <a href="{{ url_for("github.login") }}">Log in</a>
    {% endif %}
    </body>

For this to work properly, you must also do these things:

1.  Register an application with GitHub, where the "authorization callback URL"
    is ``http://localhost:5000/login/github/authorized``
2.  Replace ``my-key-here`` and ``my-secret-here`` with the client ID
    and client secret that you got from your GitHub application
3.  Install ``Flask-Dance``, ``Flask-SQLAlchemy``, ``Flask-Login``, and ``blinker``
4.  Run ``python multi.py --setup`` to create your sqlite database
5.  Set the :envvar:`OAUTHLIB_INSECURE_TRANSPORT` environment variable, so
    OAuthlib doesn't complain about running over ``http`` (for testing only!)
6.  Run ``python multi.py`` to run the application, and visit
    ``http://localhost:5000`` in your browser.

Explanation
-----------
There's a lot going on here, so let's break it down. This code uses Flask-Dance,
`Flask-SQLAlchemy`_ for a database, and `Flask-Login`_ for user management. It
also hooks into several signals, powered by the `blinker`_ library.

.. code-block:: python

    # setup Flask application
    app = Flask(__name__)
    app.secret_key = "supersekrit"
    blueprint = make_github_blueprint(
        client_id="my-key-here",
        client_secret="my-secret-here",
    )
    app.register_blueprint(blueprint, url_prefix="/login")

This is the standard pattern for creating a Flask-Dance blueprint and attaching
it to your Flask application.

.. code-block:: python

    # setup database models
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///multi.db"
    db = SQLAlchemy()

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(256), unique=True)
        # ... other columns as needed

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

This code sets up `Flask-SQLAlchemy`_, and configures it to use a sqlite database
called ``multi.db``. You can change this to use any database that `SQLAlchemy`_
supports. This code also defines two database models: a :class:`User` model
that inherits from :class:`flask_login.UserMixin` (to ensure it has the
methods that Flask-Login expects), and an :class:`OAuth` model for actually
storing OAuth tokens.

.. code-block:: python

    # setup login manager
    login_manager = LoginManager()
    login_manager.login_view = 'github.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

This code sets up `Flask-Login`_, informing it about our :class:`User` model
and the "github.login" view, so that it can properly redirect users if they
try to access views that are login-protected.

.. code-block:: python

    # setup SQLAlchemy backend
    blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user)

This code hooks up the
:class:`~flask_dance.consumer.backend.sqla.SQLAlchemyBackend` backend
to Flask-Dance, so that it can store OAuth tokens in the database.
Notice that we also pass ``user=current_user``, where :attr:`current_user`
is a proxy provided by `Flask-Login`_. This will ensure that OAuth tokens
are scoped to individual users.

.. code-block:: python

    # create/login local user on successful OAuth login
    @oauth_authorized.connect_via(blueprint)
    def github_logged_in(blueprint, token):
        if not token:
            flash("Failed to log in with {name}".format(name=blueprint.name))
            return
        # figure out who the user is
        resp = blueprint.session.get("/user")
        if resp.ok:
            username = resp.json()["login"]
            query = User.query.filter_by(username=username)
            try:
                user = query.one()
            except NoResultFound:
                # create a user
                user = User(username=username)
                db.session.add(user)
                db.session.commit()
            login_user(user)
            flash("Successfully signed in with GitHub")
        else:
            msg = "Failed to fetch user info from {name}".format(name=blueprint.name)
            flash(msg, category="error")

This code hooks into the :data:`~flask_dance.consumer.oauth_authorized` signal,
which is triggered when a user successfully completes the OAuth dance.
We make an HTTP request to GitHub using :attr:`blueprint.session`,
which already has the OAuth token loaded, in order to determine some
basic information for the user, like their GitHub username. Then we look up
in our local database to see if we already have a user with that username --
if not, we create a new user. We then log that user in, using Flask-Login's
:func:`~flask_dance.login_user` function.

We also use the :func:`~flask.flash` function to display status messages to the
user, so that they understand that they've just logged in. Good feedback to the
user is crucial for a good user experience.

.. code-block:: python

    # notify on OAuth provider error
    @oauth_error.connect_via(blueprint)
    def github_error(blueprint, error, error_description=None, error_uri=None):
        msg = (
            "OAuth error from {name}! "
            "error={error} description={description} uri={uri}"
        ).format(
            name=blueprint.name,
            error=error,
            description=error_description,
            uri=error_uri,
        )
        flash(msg, category="error")

Sometimes, the OAuth provider may throw an error message instead of allowing
the OAuth dance to complete successfully. If so, Flask-Dance will redirect the
user just as though the dance *did* complete successfully, so it is crucial
to provide feedback to the user by hooking into the
:data:`~flask_dance.consumer.oauth_error` signal.

.. code-block:: python

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have logged out")
        return redirect(url_for("index"))

    @app.route("/")
    def index():
        return render_template("home.html")

This code sets up some routes for our application: a ``logout`` route, so that
users can choose to log out of their user account, and an ``index`` route,
so that there's something to see in the application.

.. code-block:: python

    # hook up extensions to app
    db.init_app(app)
    login_manager.init_app(app)

Since we set up the Flask-SQLAlchemy and Flask-Login extensions initally
without passing the application object, we have to pass the app to them after
they've been fully configured. This is called the
:ref:`application factory pattern <app-factories>`.

.. code-block:: python

    if __name__ == "__main__":
        if "--setup" in sys.argv:
            with app.app_context():
                db.create_all()
                db.session.commit()
                print("Database tables created")
        else:
            app.run(debug=True)

We need a way to set up the database tables before the application is run,
so this code checks for a ``--setup`` flag when running the code, and if so
it sets up the database tables instead of running the application. Note that
the application is running in debug mode -- be sure to turn this off before
running your application in production!

.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Flask-SQLAlchemy: http://pythonhosted.org/Flask-SQLAlchemy/
.. _Flask-Login: https://flask-login.readthedocs.org/
.. _blinker: http://pythonhosted.org//blinker/
