import os
import pytest
import responses
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.orm.exc import NoResultFound
from flask_cache import Cache
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.models import OAuthMixin

pytestmark = [
    pytest.mark.skipif("DATABASE_URI" not in os.environ,
                       reason="DATABASE_URI required"),
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
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URI"]
    app.config["CACHE_TYPE"] = "simple"
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")
    db.init_app(app)
    # establish app context
    ctx = app.app_context()
    ctx.push()
    request.addfinalizer(ctx.pop)
    return app


def test_model(app, db, blueprint, request):

    class OAuth(db.Model, OAuthMixin):
        pass

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session)

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    queries = []
    @event.listens_for(db.engine, "before_cursor_execute")
    def record_query(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

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


def test_model_with_user(app, db, blueprint, request):

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))

    class OAuth(db.Model, OAuthMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session, lambda: User.query.first())

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    # for now, we'll assume that Alice is the only user
    alice = User(name="Alice")
    db.session.add(alice)
    db.session.commit()

    queries = []
    @event.listens_for(db.engine, "before_cursor_execute")
    def record_query(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

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

    assert len(queries) == 5

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


def test_model_repeated_token(app, db, blueprint, request):

    class OAuth(db.Model, OAuthMixin):
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

    queries = []
    @event.listens_for(db.engine, "before_cursor_execute")
    def record_query(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

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

    class OAuth(db.Model, OAuthMixin):
        pass

    blueprint.set_token_storage_sqlalchemy(OAuth, db.session, cache=cache)

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    queries = []
    @event.listens_for(db.engine, "before_cursor_execute")
    def record_query(conn, cursor, statement, parameters, context, executemany):
        queries.append(statement)

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
    queries = []
    assert blueprint.token == expected_token
    assert len(queries) == 1

    # should now be in the cache
    assert cache.get("flask_dance_token|test-service|None") == expected_token

    # subsequent references should not generate SQL queries
    queries = []
    assert blueprint.token == expected_token
    assert len(queries) == 0
    assert blueprint.get_token() == expected_token
    assert len(queries) == 0

