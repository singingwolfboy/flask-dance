from __future__ import unicode_literals

import pytest
import mock
import responses
from flask import Flask
from urlobject import URLObject
from flask_dance.contrib.okta import make_okta_blueprint, okta
from flask_dance.consumer import OAuth2ConsumerBlueprint
from oauthlib.oauth1.rfc5849.utils import parse_authorization_header
from flask_dance.consumer.backend import MemoryBackend


def test_blueprint_factory():
    okta_bp = make_okta_blueprint(
        client_id="foo",
        client_secret="bar",
        base_url="https://dev.oktapreview.com",
        scope="openid:email:profile",
        redirect_to="index",
        authorization_url="https://dev.oktapreview.com/oauth2/default/v1/authorize",
        token_url="https://dev.oktapreview.com/oauth2/default/v1/token"
    )
    assert isinstance(okta_bp, OAuth2ConsumerBlueprint)
    assert okta_bp.session.scope == "openid:email:profile"
    assert okta_bp.session.base_url == "https://dev.oktapreview.com"
    assert okta_bp.session.client_id == "foo"
    assert okta_bp.client_secret == "bar"
    assert okta_bp.authorization_url == "https://dev.oktapreview.com/oauth2/default/v1/authorize"
    assert okta_bp.token_url == "https://dev.oktapreview.com/oauth2/default/v1/token"


def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["OKTA_OAUTH_CLIENT_ID"] = "foo"
    app.config["OKTA_OAUTH_CLIENT_SECRET"] = "bar"
    okta_bp = make_okta_blueprint(
        client_id="foo",
        client_secret="bar",
        base_url="https://dev.oktapreview.com",
        scope="openid:email:profile",
        redirect_to="index",
        authorization_url="https://dev.oktapreview.com/oauth2/default/v1/authorize",
        token_url="https://dev.oktapreview.com/oauth2/default/v1/token"
    )
    app.register_blueprint(okta_bp)

    resp = app.test_client().get("/okta")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    okta_bp1 = make_okta_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(okta_bp1)

    app2 = Flask(__name__)
    okta_bp2 = make_okta_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(okta_bp2)

    # outside of a request context, referencing functions on the `github` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        okta.get("https://google.com")

    # inside of a request context, `github` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        okta.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        okta.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"