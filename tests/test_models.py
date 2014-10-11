import os
import pytest
import responses
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.models import OAuthMixin

pytestmark = pytest.mark.skipif("DATABASE_URI" not in os.environ,
                                reason="DATABASE_URI required")


@pytest.mark.usefixtures("responses")
def test_model(request):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URI"]
    db = SQLAlchemy(app)

    class OAuth(db.Model, OAuthMixin):
        pass

    blueprint = OAuth2ConsumerBlueprint("test-service", __name__,
        client_id="client_id",
        client_secret="client_secret",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_url="/oauth_done",
    )
    blueprint.set_token_storage_sqlalchemy(OAuth, db.session)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":""}',
    )
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


@pytest.mark.usefixtures("responses")
def test_model_with_user(request):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URI"]
    db = SQLAlchemy(app)

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))

    class OAuth(db.Model, OAuthMixin):
        user_id = db.Column(db.Integer, db.ForeignKey(User.id))
        user = db.relationship(User)

    blueprint = OAuth2ConsumerBlueprint("test-service", __name__,
        client_id="client_id",
        client_secret="client_secret",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_url="/oauth_done",
    )
    blueprint.set_token_storage_sqlalchemy(OAuth, db.session, lambda: User.query.first())
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    db.create_all()
    def done():
        db.session.remove()
        db.drop_all()
    request.addfinalizer(done)

    # for now, we'll assume that Alice is the only user
    alice = User(name="Alice")
    db.session.add(alice)
    db.session.commit()

    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":""}',
    )
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

