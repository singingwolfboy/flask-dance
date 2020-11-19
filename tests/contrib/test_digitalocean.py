from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.digitalocean import make_digitalocean_blueprint, digitalocean
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the digitalocean provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_digitalocean_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_scope_list_is_valid_with_single_scope():
    digitalocean_bp = make_digitalocean_blueprint(
        client_id="foobar", client_secret="supersecret", scope="read"
    )
    assert digitalocean_bp.session.scope == "read"


def test_scope_list_is_converted_to_space_delimited():
    digitalocean_bp = make_digitalocean_blueprint(
        client_id="foobar", client_secret="supersecret", scope="read,write"
    )
    assert digitalocean_bp.session.scope == "read write"


def test_blueprint_factory():
    digitalocean_bp = make_digitalocean_blueprint(
        client_id="foobar", client_secret="supersecret"
    )
    assert isinstance(digitalocean_bp, OAuth2ConsumerBlueprint)
    assert digitalocean_bp.session.client_id == "foobar"
    assert digitalocean_bp.client_secret == "supersecret"
    assert digitalocean_bp.token_url == "https://cloud.digitalocean.com/v1/oauth/token"
    assert (
        digitalocean_bp.authorization_url
        == "https://cloud.digitalocean.com/v1/oauth/authorize"
    )


@responses.activate
def test_load_from_config(make_app):
    app = make_app()
    app.config["DIGITALOCEAN_OAUTH_CLIENT_ID"] = "foo"
    app.config["DIGITALOCEAN_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/digitalocean")
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
    # outside of a request context, referencing functions on the `digitalocean`
    # object will raise an exception
    with pytest.raises(RuntimeError):
        digitalocean.get("https://google.com")
    # inside of a request context, `digitalocean` should be a proxy to the
    # correct blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        digitalocean.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"
    with app2.test_request_context("/"):
        app2.preprocess_request()
        digitalocean.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
