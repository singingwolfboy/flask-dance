from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.instagram import make_instagram_blueprint, instagram
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the Instagram provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "supersecret"
        blueprint = make_instagram_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory():
    instagram_bp = make_instagram_blueprint(
        client_id="foo", client_secret="bar", scope="basic", redirect_to="index"
    )
    assert isinstance(instagram_bp, OAuth2ConsumerBlueprint)
    assert instagram_bp.session.scope == "basic"
    assert instagram_bp.session.base_url == "https://api.instagram.com/v1/"
    assert instagram_bp.session.client_id == "foo"
    assert instagram_bp.client_secret == "bar"
    assert (
        instagram_bp.authorization_url == "https://api.instagram.com/oauth/authorize/"
    )
    assert instagram_bp.token_url == "https://api.instagram.com/oauth/access_token"


def test_load_from_config(make_app):
    app = make_app(redirect_to="index")
    app.config["INSTAGRAM_OAUTH_CLIENT_ID"] = "foo"
    app.config["INSTAGRAM_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/instagram")
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

    # outside of a request context, referencing functions on the `instagram` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        instagram.get("https://google.com")

    # inside of a request context, `instagram` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        instagram.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        instagram.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
