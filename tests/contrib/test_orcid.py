import pytest
import responses
from flask import Flask
from urlobject import URLObject

from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage
from flask_dance.contrib.orcid import make_orcid_blueprint, orcid


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the ORCID provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_orcid_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory():
    orcid_bp = make_orcid_blueprint(
        client_id="foo", client_secret="bar", scope="user:email", redirect_to="index"
    )
    assert isinstance(orcid_bp, OAuth2ConsumerBlueprint)
    assert orcid_bp.session.scope == "user:email"
    assert orcid_bp.session.base_url == "https://api.orcid.org"
    assert orcid_bp.session.client_id == "foo"
    assert orcid_bp.client_secret == "bar"
    assert orcid_bp.authorization_url == "https://orcid.org/oauth/authorize"
    assert orcid_bp.token_url == "https://orcid.org/oauth/token"


def test_sandbox_blueprint_factory():
    orcid_bp = make_orcid_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="user:email",
        redirect_to="index",
        sandbox=True,
    )
    assert isinstance(orcid_bp, OAuth2ConsumerBlueprint)
    assert orcid_bp.session.scope == "user:email"
    assert orcid_bp.session.base_url == "https://api.sandbox.orcid.org"
    assert orcid_bp.session.client_id == "foo"
    assert orcid_bp.client_secret == "bar"
    assert orcid_bp.authorization_url == "https://sandbox.orcid.org/oauth/authorize"
    assert orcid_bp.token_url == "https://sandbox.orcid.org/oauth/token"


def test_load_from_config(make_app):
    app = make_app()
    app.config["ORCID_OAUTH_CLIENT_ID"] = "foo"
    app.config["ORCID_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/orcid")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


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

    # outside of a request context, referencing functions on the `orcid` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        orcid.get("https://google.com")

    # inside of a request context, `orcid` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        orcid.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        orcid.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
