from __future__ import unicode_literals

import pytest
import responses
from flask import Flask
from urlobject import URLObject

from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage
from flask_dance.contrib.authentiq import make_authentiq_blueprint, authentiq


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the Authentiq provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_authentiq_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory_default():
    # Test with connect.authentiq.io
    aqbp = make_authentiq_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="openid profile",
        redirect_to="index",
    )
    assert isinstance(aqbp, OAuth2ConsumerBlueprint)
    assert aqbp.session.scope == "openid profile"
    assert aqbp.session.base_url == "https://connect.authentiq.io/"
    assert aqbp.session.client_id == "foo"
    assert aqbp.client_secret == "bar"
    assert aqbp.authorization_url == "https://connect.authentiq.io/authorize"
    assert aqbp.token_url == "https://connect.authentiq.io/token"


def test_blueprint_factory_custom():
    aqbp = make_authentiq_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="openid profile",
        redirect_to="index",
        hostname="local.example.com",
    )
    assert isinstance(aqbp, OAuth2ConsumerBlueprint)
    assert aqbp.session.scope == "openid profile"
    assert aqbp.session.base_url == "https://local.example.com/"
    assert aqbp.session.client_id == "foo"
    assert aqbp.client_secret == "bar"
    assert aqbp.authorization_url == "https://local.example.com/authorize"
    assert aqbp.token_url == "https://local.example.com/token"


def test_load_from_config(make_app):
    app = make_app(redirect_to="index")
    app.config["AUTHENTIQ_OAUTH_CLIENT_ID"] = "foo"
    app.config["AUTHENTIQ_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/authentiq")
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

    # outside of a request context, referencing functions on the `authentiq`
    # object will raise an exception
    with pytest.raises(RuntimeError):
        authentiq.get("https://google.com")

    # inside of a request context, `authentiq` should be a proxy to the
    # correct blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        authentiq.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        authentiq.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
