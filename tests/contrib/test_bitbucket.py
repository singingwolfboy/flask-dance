from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.bitbucket import make_bitbucket_blueprint, bitbucket
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend


def test_blueprint_factory():
    bitbucket_bp = make_bitbucket_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="user:email",
        redirect_to="index",
    )
    assert isinstance(bitbucket_bp, OAuth2ConsumerBlueprint)
    assert bitbucket_bp.session.scope == "user:email"
    assert bitbucket_bp.session.base_url == "https://bitbucket.org/"
    assert bitbucket_bp.session.client_id == "foo"
    assert bitbucket_bp.client_secret == "bar"
    assert bitbucket_bp.authorization_url == "https://bitbucket.org/site/oauth2/authorize"
    assert bitbucket_bp.token_url == "https://bitbucket.org/site/oauth2/access_token"


def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["BITBUCKET_OAUTH_CLIENT_ID"] = "foo"
    app.config["BITBUCKET_OAUTH_CLIENT_SECRET"] = "bar"
    bitbucket_bp = make_bitbucket_blueprint(redirect_to="index")
    app.register_blueprint(bitbucket_bp)

    resp = app.test_client().get("/bitbucket")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    ghbp1 = make_bitbucket_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(ghbp1)

    app2 = Flask(__name__)
    ghbp2 = make_bitbucket_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(ghbp2)

    # outside of a request context, referencing functions on the `bitbucket` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        bitbucket.get("https://google.com")

    # inside of a request context, `bitbucket` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        bitbucket.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        bitbucket.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
