from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.zoho import make_zoho_blueprint, zoho
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend


def test_blueprint_factory():
    zoho_bp = make_zoho_blueprint(
        client_id="foobar",
        client_secret="supersecret",
    )
    assert isinstance(zoho_bp, OAuth2ConsumerBlueprint)
    assert zoho_bp.session.client_id == "foobar"
    assert zoho_bp.client_secret == "supersecret"
    assert zoho_bp.token_url == "https://accounts.zoho.com/oauth/v2/token"
    assert zoho_bp.authorization_url == "https://accounts.zoho.com/oauth/v2/auth"


@responses.activate
def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["ZOHO_OAUTH_CLIENT_ID"] = "foo"
    app.config["ZOHO_OAUTH_CLIENT_SECRET"] = "bar"
    zoho_bp = make_zoho_blueprint()
    app.register_blueprint(zoho_bp)
    resp = app.test_client().get("/zoho")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_load_from_params():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["ZOHO_OAUTH_CLIENT_ID"] = "foo"
    app.config["ZOHO_OAUTH_CLIENT_SECRET"] = "bar"
    zoho_bp = make_zoho_blueprint(
        client_id="not_foo",
        client_secret="not_bar"
    )
    app.register_blueprint(zoho_bp)
    resp = app.test_client().get("/zoho")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "not_foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")
     # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    zoho_bp1 = make_zoho_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(zoho_bp1)
    app2 = Flask(__name__)
    zoho_bp2 = make_zoho_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(zoho_bp2)
    # outside of a request context, referencing functions on the `zoho` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        zoho.get("https://google.com")
    # inside of a request context, `zoho` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        zoho.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Zoho-oauthtoken app1"
    with app2.test_request_context("/"):
        app2.preprocess_request()
        zoho.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Zoho-oauthtoken app2"
