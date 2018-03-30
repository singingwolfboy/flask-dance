from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.vk import make_vk_blueprint, vk
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend


def test_blueprint_factory():
    vk_bp = make_vk_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="email",
        redirect_to="index",
    )
    assert isinstance(vk_bp, OAuth2ConsumerBlueprint)
    assert vk_bp.session.scope == "email"
    assert vk_bp.session.base_url == "https://api.vk.com/"
    assert vk_bp.session.client_id == "foo"
    assert vk_bp.client_secret == "bar"
    assert vk_bp.authorization_url == "https://oauth.vk.com/authorize"
    assert vk_bp.token_url == "https://oauth.vk.com/access_token"


def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["VK_OAUTH_CLIENT_ID"] = "foo"
    app.config["VK_OAUTH_CLIENT_SECRET"] = "bar"
    github_bp = make_vk_blueprint(redirect_to="index")
    app.register_blueprint(github_bp)

    resp = app.test_client().get("/vk")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    ghbp1 = make_vk_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(ghbp1)

    app2 = Flask(__name__)
    ghbp2 = make_vk_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(ghbp2)

    # outside of a request context, referencing functions on the `github` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        vk.get("https://google.com")

    # inside of a request context, `github` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        vk.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        vk.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
