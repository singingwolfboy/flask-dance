from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.nylas import make_nylas_blueprint, nylas
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the Nylas provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_nylas_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory():
    nylas_bp = make_nylas_blueprint(
        client_id="foo", client_secret="bar", redirect_to="index"
    )
    assert isinstance(nylas_bp, OAuth2ConsumerBlueprint)
    assert nylas_bp.session.scope == "email"
    assert nylas_bp.session.base_url == "https://api.nylas.com/"
    assert nylas_bp.session.client_id == "foo"
    assert nylas_bp.client_secret == "bar"
    assert nylas_bp.authorization_url == "https://api.nylas.com/oauth/authorize"
    assert nylas_bp.token_url == "https://api.nylas.com/oauth/token"


def test_load_from_config(make_app):
    app = make_app()
    app.config["NYLAS_OAUTH_CLIENT_ID"] = "foo"
    app.config["NYLAS_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/nylas")
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

    # outside of a request context, referencing functions on the `nylas` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        nylas.get("https://google.com")

    # inside of a request context, `nylas` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        nylas.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        nylas.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
