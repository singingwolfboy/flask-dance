import os
import pytest
import responses
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.orm.exc import NoResultFound
from flask_cache import Cache
from flask_login import LoginManager, UserMixin, current_user, login_user
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.models import OAuthConsumerMixin

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
    app = Flask(__name__)
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


def test_model(app, db, blueprint, request):

    class OAuth(db.Model, OAuthConsumerMixin):
        pass

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session)

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

    assert len(queries) == 3

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


def test_model_repr(app, db, request):
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


def test_model_with_user(app, db, blueprint, request):

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

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session, user=alice)

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

    assert len(queries) == 4

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

def test_model_with_flask_login(app, db, blueprint, request):
    login_manager = LoginManager(app)

    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))

    class OAuth(db.Model, OAuthConsumerMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session, user=current_user)

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


def test_model_repeated_token(app, db, blueprint, request):

    class OAuth(db.Model, OAuthConsumerMixin):
        pass

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session)

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

    assert len(queries) == 3

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


def test_model_with_cache(app, db, blueprint, request):
    cache = Cache(app)

    class OAuth(db.Model, OAuthConsumerMixin):
        pass

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session, cache=cache)

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

    assert len(queries) == 3

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
    with record_queries(db.engine) as queries:
        assert blueprint.get_token() == expected_token
    assert len(queries) == 0
