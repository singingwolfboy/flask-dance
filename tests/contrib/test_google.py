from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the Google provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_google_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory():
    google_bp = make_google_blueprint(
        client_id="foo", client_secret="bar", redirect_to="index"
    )
    assert isinstance(google_bp, OAuth2ConsumerBlueprint)
    assert google_bp.session.scope == [
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
    assert google_bp.session.base_url == "https://www.googleapis.com/"
    assert google_bp.session.client_id == "foo"
    assert google_bp.client_secret == "bar"
    assert google_bp.authorization_url == "https://accounts.google.com/o/oauth2/auth"
    assert google_bp.token_url == "https://accounts.google.com/o/oauth2/token"
    assert google_bp.auto_refresh_url is None


def test_load_from_config(make_app):
    app = make_app(redirect_to="index")
    app.config["GOOGLE_OAUTH_CLIENT_ID"] = "foo"
    app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/google")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


def test_blueprint_factory_scope():
    google_bp = make_google_blueprint(
        client_id="foo", client_secret="bar", scope="customscope", redirect_to="index"
    )
    assert google_bp.session.scope == "customscope"


def test_blueprint_factory_offline():
    google_bp = make_google_blueprint(
        client_id="foo", client_secret="bar", redirect_to="index", offline=True
    )
    assert google_bp.auto_refresh_url == "https://accounts.google.com/o/oauth2/token"


def test_blueprint_factory_hosted_domain():
    google_bp = make_google_blueprint(
        client_id="foo",
        client_secret="bar",
        redirect_to="index",
        hosted_domain="example.com",
    )

    assert google_bp.authorization_url_params["hd"] == "example.com"


@responses.activate
def test_context_local(make_app):
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = make_app(
        "foo1",
        "bar1",
        redirect_to="url1",
        storage=MemoryStorage({"access_token": "app1"}),
    )
    app2 = make_app(
        "foo2",
        "bar2",
        redirect_to="url2",
        storage=MemoryStorage({"access_token": "app2"}),
    )

    # outside of a request context, referencing functions on the `google` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        google.get("https://github.com")

    # inside of a request context, `google` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        google.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        google.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"


def test_offline(make_app):
    app = make_app("foo", "bar", offline=True)

    with app.test_client() as client:
        resp = client.get("/google", base_url="https://a.b.c", follow_redirects=False)
    # check that there is a `access_type=offline` query param in the redirect URL
    assert resp.status_code == 302
    location = URLObject(resp.headers["Location"])
    assert location.query_dict["access_type"] == "offline"


def test_hd(make_app):
    app = make_app("foo", "bar", hosted_domain="example.com")

    with app.test_client() as client:
        resp = client.get("/google", base_url="https://a.b.c", follow_redirects=False)
    # check that there is a `hd=example.com` query param in the redirect URL
    assert resp.status_code == 302
    location = URLObject(resp.headers["Location"])
    assert location.query_dict["hd"] == "example.com"


def test_offline_consent(make_app):
    app = make_app("foo", "bar", offline=True, reprompt_consent=True)

    with app.test_client() as client:
        resp = client.get("/google", base_url="https://a.b.c", follow_redirects=False)
    assert resp.status_code == 302
    location = URLObject(resp.headers["Location"])
    assert location.query_dict["access_type"] == "offline"
    assert location.query_dict["prompt"] == "consent"


def test_offline_select_account(make_app):
    app = make_app("foo", "bar", offline=True, reprompt_select_account=True)

    with app.test_client() as client:
        resp = client.get("/google", base_url="https://a.b.c", follow_redirects=False)
    assert resp.status_code == 302
    location = URLObject(resp.headers["Location"])
    assert location.query_dict["access_type"] == "offline"
    assert location.query_dict["prompt"] == "select_account"


def test_offline_select_account_and_consent(make_app):
    app = make_app(
        "foo", "bar", offline=True, reprompt_consent=True, reprompt_select_account=True
    )

    with app.test_client() as client:
        resp = client.get("/google", base_url="https://a.b.c", follow_redirects=False)
    assert resp.status_code == 302
    location = URLObject(resp.headers["Location"])
    assert location.query_dict["access_type"] == "offline"
    assert location.query_dict["prompt"] == "consent select_account"
