import pytest
sa = pytest.importorskip("sqlalchemy")

import os
import responses
import flask
from lazy import lazy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.orm.exc import NoResultFound
from flask_cache import Cache
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from flask_dance.consumer import OAuth2ConsumerBlueprint, oauth_authorized
from flask_dance.consumer.backend.sqla import OAuthConsumerMixin, SQLAlchemyBackend
try:
    import blinker
except ImportError:
    blinker = None
requires_blinker = pytest.mark.skipif(not blinker, reason="requires blinker")

pytestmark = [
    pytest.mark.usefixtures("responses"),
]


@pytest.fixture
def blueprint():
    bp = OAuth2ConsumerBlueprint("test-service", __name__,
        client_id="client_id",
        client_secret="client_secret",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_url="/oauth_done",
    )
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":""}',
    )
    return bp


@pytest.fixture
def db():
    return SQLAlchemy()


@pytest.fixture
def app(blueprint, db, request):
    app = flask.Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URI", "sqlite://")
    app.config["CACHE_TYPE"] = "simple"
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")
    db.init_app(app)
    # establish app context
    ctx = app.app_context()
    ctx.push()
    request.addfinalizer(ctx.pop)
    return app


class record_queries(object):
    """
    A context manager for recording the SQLAlchemy queries that were executed
    in a given context block.
    """
    def __init__(self, target, identifier="before_cursor_execute"):
        self.target = target
        self.identifier = identifier

    def record_query(self, conn, cursor, statement, parameters, context, executemany):
        self.queries.append(statement)

    def __enter__(self):
        self.queries = []
        event.listen(self.target, self.identifier, self.record_query)
        return self.queries

    def __exit__(self, exc_type, exc_value, traceback):
        event.remove(self.target, self.identifier, self.record_query)


def test_sqla_backend_without_user(app, db, blueprint, request):

    class OAuth(db.Model, OAuthConsumerMixin):
        pass

    blueprint.backend = SQLAlchemyBackend(OAuth, db.session)

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    with record_queries(db.engine) as queries:
        with app.test_client() as client:
            # reset the session before the request
            with client.session_transaction() as sess:
                sess["test-service_oauth_state"] = "random-string"
            # make the request
            resp = client.get(
                "/login/test-service/authorized?code=secret-code&state=random-string",
                base_url="https://a.b.c",
            )
            # check that we redirected the client
            assert resp.status_code == 302
            assert resp.headers["Location"] == "https://a.b.c/oauth_done"

    assert len(queries) == 2

    # check the database
    authorizations = OAuth.query.all()
    assert len(authorizations) == 1
    oauth = authorizations[0]
    assert oauth.provider == "test-service"
    assert isinstance(oauth.token, dict)
    assert oauth.token == {
        "access_token": "foobar",
        "token_type": "bearer",
        "scope": [""],
    }


def test_sqla_model_repr(app, db, request):
    class MyAwesomeOAuth(db.Model, OAuthConsumerMixin):
        pass

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    o = MyAwesomeOAuth()
    assert "MyAwesomeOAuth" in repr(o)
    o.provider = "supercool"
    assert 'provider="supercool"' in repr(o)
    o.token = {"access_token": "secret"}
    assert "secret" not in repr(o)

    db.session.add(o)
    db.session.commit()
    assert "id=" in repr(o)
    assert "secret" not in repr(o)


def test_sqla_backend(app, db, blueprint, request):

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    # for now, we'll assume that Alice is the only user
    alice = User(name="Alice")
    db.session.add(alice)
    db.session.commit()
    # load alice's ID -- this issues a database query
    alice.id

    blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=alice)

    with record_queries(db.engine) as queries:
        with app.test_client() as client:
            # reset the session before the request
            with client.session_transaction() as sess:
                sess["test-service_oauth_state"] = "random-string"
            # make the request
            resp = client.get(
                "/login/test-service/authorized?code=secret-code&state=random-string",
                base_url="https://a.b.c",
            )
            # check that we redirected the client
            assert resp.status_code == 302
            assert resp.headers["Location"] == "https://a.b.c/oauth_done"

    assert len(queries) == 3

    # check the database
    alice = User.query.first()
    authorizations = OAuth.query.all()
    assert len(authorizations) == 1
    oauth = authorizations[0]
    assert oauth.user_id == alice.id
    assert oauth.provider == "test-service"
    assert isinstance(oauth.token, dict)
    assert oauth.token == {
        "access_token": "foobar",
        "token_type": "bearer",
        "scope": [""],
    }


def test_sqla_load_token_for_user(app, db, blueprint, request):

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    # set token storage
    blueprint.backend = SQLAlchemyBackend(OAuth, db.session)

    # make users and OAuth tokens for several people
    alice = User(name="Alice")
    alice_token = {"access_token": "alice123", "token_type": "bearer"}
    alice_oauth = OAuth(user=alice, token=alice_token, provider="test-service")
    bob = User(name="Bob")
    bob_token = {"access_token": "bob456", "token_type": "bearer"}
    bob_oauth = OAuth(user=bob, token=bob_token, provider="test-service")
    sue = User(name="Sue")
    sue_token = {"access_token": "sue789", "token_type": "bearer"}
    sue_oauth = OAuth(user=sue, token=sue_token, provider="test-service")
    db.session.add_all([alice, bob, sue, alice_oauth, bob_oauth, sue_oauth])
    db.session.commit()

    # by default, we should not have a token for anyone
    sess = blueprint.session
    assert not sess.token
    assert not blueprint.token

    # load token for various users
    blueprint.config["user"] = alice
    assert sess.token == alice_token
    assert blueprint.token == alice_token

    blueprint.config["user"] = bob
    assert sess.token == bob_token
    assert blueprint.token == bob_token

    blueprint.config["user"] = alice
    assert sess.token == alice_token
    assert blueprint.token == alice_token

    blueprint.config["user"] = sue
    assert sess.token == sue_token
    assert blueprint.token == sue_token

    # load for user ID as well
    del blueprint.config["user"]
    blueprint.config["user_id"] = bob.id
    assert sess.token == bob_token
    assert blueprint.token == bob_token

    # try deleting user tokens
    del blueprint.token
    assert sess.token == None
    assert blueprint.token == None

    # shouldn't affect alice's token
    blueprint.config["user_id"] = alice.id
    assert sess.token == alice_token
    assert blueprint.token == alice_token

def test_sqla_flask_login(app, db, blueprint, request):
    login_manager = LoginManager(app)

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user)

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    # create some users
    u1 = User(name="Alice")
    u2 = User(name="Bob")
    u3 = User(name="Chuck")
    db.session.add_all([u1, u2, u3])
    db.session.commit()

    # configure login manager
    @login_manager.user_loader
    def load_user(userid):
        return User.query.get(userid)

    with record_queries(db.engine) as queries:
        with app.test_client() as client:
            # reset the session before the request
            with client.session_transaction() as sess:
                sess["test-service_oauth_state"] = "random-string"
                # set alice as the logged in user
                sess["user_id"] = u1.id
            # make the request
            resp = client.get(
                "/login/test-service/authorized?code=secret-code&state=random-string",
                base_url="https://a.b.c",
            )
            # check that we redirected the client
            assert resp.status_code == 302
            assert resp.headers["Location"] == "https://a.b.c/oauth_done"

    assert len(queries) == 4

    # lets do it again, with Bob as the logged in user -- he gets a different token
    responses.reset()
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"abcdef","token_type":"bearer","scope":"bob"}',
    )
    with record_queries(db.engine) as queries:
        with app.test_client() as client:
            # reset the session before the request
            with client.session_transaction() as sess:
                sess["test-service_oauth_state"] = "random-string"
                # set bob as the logged in user
                sess["user_id"] = u2.id
            # make the request
            resp = client.get(
                "/login/test-service/authorized?code=secret-code&state=random-string",
                base_url="https://a.b.c",
            )
            # check that we redirected the client
            assert resp.status_code == 302
            assert resp.headers["Location"] == "https://a.b.c/oauth_done"

    assert len(queries) == 4

    # check the database
    authorizations = OAuth.query.all()
    assert len(authorizations) == 2
    u1_oauth = OAuth.query.filter_by(user=u1).one()
    assert u1_oauth.provider == "test-service"
    assert u1_oauth.token == {
        "access_token": "foobar",
        "token_type": "bearer",
        "scope": [""],
    }
    u2_oauth = OAuth.query.filter_by(user=u2).one()
    assert u2_oauth.provider == "test-service"
    assert u2_oauth.token == {
        "access_token": "abcdef",
        "token_type": "bearer",
        "scope": ["bob"],
    }
    u3_oauth = OAuth.query.filter_by(user=u3).all()
    assert len(u3_oauth) == 0


@requires_blinker
def test_sqla_flask_login_anon_to_authed(app, db, blueprint, request):
    login_manager = LoginManager(app)

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user)

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    # configure login manager
    @login_manager.user_loader
    def load_user(userid):
        return User.query.get(userid)

    # create a user object when OAuth succeeds
    def logged_in(sender, token):
        assert token
        assert blueprint == sender
        resp = sender.session.get("/user")
        user = User(name=resp.json()["name"])
        login_user(user)
        db.session.add(user)
        db.session.commit()
        flask.flash("Signed in successfully")

    oauth_authorized.connect(logged_in, blueprint)
    request.addfinalizer(lambda: oauth_authorized.disconnect(logged_in, blueprint))

    # mock out the `/user` API call
    responses.add(
        responses.GET,
        "https://example.com/user",
        body='{"name":"josephine"}',
    )

    with record_queries(db.engine) as queries:
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["test-service_oauth_state"] = "random-string"
            # make the request
            resp = client.get(
                "/login/test-service/authorized?code=secret-code&state=random-string",
                base_url="https://a.b.c",
            )
            # check that we redirected the client
            assert resp.status_code == 302
            assert resp.headers["Location"] == "https://a.b.c/oauth_done"

    assert len(queries) == 5

    # check the database
    users = User.query.all()
    assert len(users) == 1
    user = users[0]
    assert user.name == "josephine"

    authorizations = OAuth.query.all()
    assert len(authorizations) == 1
    oauth = authorizations[0]
    assert oauth.provider == "test-service"
    assert oauth.token == {
        "access_token": "foobar",
        "token_type": "bearer",
        "scope": [""],
    }
    assert oauth.user_id == user.id


def test_sqla_flask_login_preload_logged_in_user(app, db, blueprint, request):
    # need a URL to hit, so that tokens will be loaded, but result is irrelevant
    responses.add(
        responses.GET,
        "https://example.com/noop",
    )

    login_manager = LoginManager(app)

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    blueprint.backend = SQLAlchemyBackend(OAuth, db.session, user=current_user)

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    # create some users, and tokens for some of them
    alice = User(name="Alice")
    alice_token = {"access_token": "alice123", "token_type": "bearer"}
    alice_oauth = OAuth(user=alice, token=alice_token, provider="test-service")
    bob = User(name="Bob")
    bob_token = {"access_token": "bob456", "token_type": "bearer"}
    bob_oauth = OAuth(user=bob, token=bob_token, provider="test-service")
    chuck = User(name="Chuck")
    # chuck doesn't get a token
    db.session.add_all([alice, alice_oauth, bob, bob_oauth, chuck])
    db.session.commit()

    # configure login manager
    @login_manager.user_loader
    def load_user(userid):
        return User.query.get(userid)

    # create a simple view
    @app.route("/")
    def index():
        return "success"

    with app.test_request_context("/"):
        login_user(alice)
        # hit /noop to load tokens
        blueprint.session.get("/noop")
        # now the flask-dance session should have Alice's token loaded
        assert blueprint.session.token == alice_token

    with app.test_request_context("/"):
        # set bob as the logged in user
        login_user(bob)
        # hit /noop to load tokens
        blueprint.session.get("/noop")
        # now the flask-dance session should have Bob's token loaded
        assert blueprint.session.token == bob_token

    with app.test_request_context("/"):
        # now let's try chuck
        login_user(chuck)
        blueprint.session.get("/noop")
        assert blueprint.session.token == None

    with app.test_request_context("/"):
        # no one is logged in -- this is an anonymous user
        logout_user()
        blueprint.session.get("/noop")
        assert blueprint.session.token == None


def test_sqla_delete_token(app, db, blueprint, request):

    class OAuth(db.Model, OAuthConsumerMixin):
        pass

    blueprint.backend = SQLAlchemyBackend(OAuth, db.session)

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    # Create an existing OAuth token for the service
    existing = OAuth(
        provider="test-service",
        token={
            "access_token": "something",
            "token_type": "bearer",
            "scope": ["blah"],
        },
    )
    db.session.add(existing)
    db.session.commit()
    assert len(OAuth.query.all()) == 1

    assert blueprint.token == {
        "access_token": "something",
        "token_type": "bearer",
        "scope": ["blah"],
    }
    del blueprint.token
    assert blueprint.token == None
    assert len(OAuth.query.all()) == 0


def test_sqla_overwrite_token(app, db, blueprint, request):

    class OAuth(db.Model, OAuthConsumerMixin):
        pass

    blueprint.backend = SQLAlchemyBackend(OAuth, db.session)

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    # Create an existing OAuth token for the service
    existing = OAuth(
        provider="test-service",
        token={
            "access_token": "something",
            "token_type": "bearer",
            "scope": ["blah"],
        },
    )
    db.session.add(existing)
    db.session.commit()
    assert len(OAuth.query.all()) == 1

    with record_queries(db.engine) as queries:
        with app.test_client() as client:
            # reset the session before the request
            with client.session_transaction() as sess:
                sess["test-service_oauth_state"] = "random-string"
            # make the request
            resp = client.get(
                "/login/test-service/authorized?code=secret-code&state=random-string",
                base_url="https://a.b.c",
            )
            # check that we redirected the client
            assert resp.status_code == 302
            assert resp.headers["Location"] == "https://a.b.c/oauth_done"

    assert len(queries) == 2

    # check that the database record was overwritten
    authorizations = OAuth.query.all()
    assert len(authorizations) == 1
    oauth = authorizations[0]
    assert oauth.provider == "test-service"
    assert isinstance(oauth.token, dict)
    assert oauth.token == {
        "access_token": "foobar",
        "token_type": "bearer",
        "scope": [""],
    }


def test_sqla_cache(app, db, blueprint, request):
    cache = Cache(app)

    class OAuth(db.Model, OAuthConsumerMixin):
        pass

    blueprint.backend = SQLAlchemyBackend(OAuth, db.session, cache=cache)

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    with record_queries(db.engine) as queries:
        with app.test_client() as client:
            # reset the session before the request
            with client.session_transaction() as sess:
                sess["test-service_oauth_state"] = "random-string"
            # make the request
            resp = client.get(
                "/login/test-service/authorized?code=secret-code&state=random-string",
                base_url="https://a.b.c",
            )
            # check that we redirected the client
            assert resp.status_code == 302
            assert resp.headers["Location"] == "https://a.b.c/oauth_done"

    assert len(queries) == 2

    expected_token = {
        "access_token": "foobar",
        "token_type": "bearer",
        "scope": [""],
    }

    # check the database
    authorizations = OAuth.query.all()
    assert len(authorizations) == 1
    oauth = authorizations[0]
    assert oauth.provider == "test-service"
    assert isinstance(oauth.token, dict)
    assert oauth.token == expected_token

    # cache should be invalidated
    assert cache.get("flask_dance_token|test-service|None") is None

    # first reference to the token should generate SQL queries
    with record_queries(db.engine) as queries:
        assert blueprint.token == expected_token
    assert len(queries) == 1

    # should now be in the cache
    assert cache.get("flask_dance_token|test-service|None") == expected_token

    # subsequent references should not generate SQL queries
    with record_queries(db.engine) as queries:
        assert blueprint.token == expected_token
    assert len(queries) == 0
