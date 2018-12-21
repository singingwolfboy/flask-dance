from __future__ import unicode_literals

import pytest
import responses
from flask import Flask
from urlobject import URLObject

from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend
from flask_dance.contrib.authentiq import make_authentiq_blueprint, authentiq


def test_blueprint_factory_default():
    # Test with connect.authentiq.io
    aqbp1 = make_authentiq_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="openid profile",
        redirect_to="index"
    )
    assert isinstance(aqbp1, OAuth2ConsumerBlueprint)
    assert aqbp1.session.scope == "openid profile"
    assert aqbp1.session.base_url == "https://connect.authentiq.io/"
    assert aqbp1.session.client_id == "foo"
    assert aqbp1.client_secret == "bar"
    assert aqbp1.authorization_url == "https://connect.authentiq.io/authorize"
    assert aqbp1.token_url == "https://connect.authentiq.io/token"


def test_blueprint_factory_custom():
    aqbp2 = make_authentiq_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="openid profile",
        redirect_to="index",
        hostname="local.example.com"
    )
    assert isinstance(aqbp2, OAuth2ConsumerBlueprint)
    assert aqbp2.session.scope == "openid profile"
    assert aqbp2.session.base_url == "https://local.example.com/"
    assert aqbp2.session.client_id == "foo"
    assert aqbp2.client_secret == "bar"
    assert aqbp2.authorization_url == "https://local.example.com/authorize"
    assert aqbp2.token_url == "https://local.example.com/token"


def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["AUTHENTIQ_OAUTH_CLIENT_ID"] = "foo"
    app.config["AUTHENTIQ_OAUTH_CLIENT_SECRET"] = "bar"
    authentiq_bp = make_authentiq_blueprint(redirect_to="index")
    app.register_blueprint(authentiq_bp)

    resp = app.test_client().get("/authentiq")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    aqbp1 = make_authentiq_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(aqbp1)

    app2 = Flask(__name__)
    aqbp2 = make_authentiq_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(aqbp2)

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
