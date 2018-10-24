from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.reddit import make_reddit_blueprint, reddit
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend


def test_blueprint_factory():
    reddit_bp = make_reddit_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="identity",
        redirect_to="index",
    )
    assert isinstance(reddit_bp, OAuth2ConsumerBlueprint)
    assert reddit_bp.session.scope == "identity"
    assert reddit_bp.session.base_url == "https://oauth.reddit.com/"
    assert reddit_bp.session.client_id == "foo"
    assert reddit_bp.client_secret == "bar"
    assert reddit_bp.authorization_url == "https://www.reddit.com/api/v1/authorize"
    assert reddit_bp.token_url == "https://www.reddit.com/api/v1/access_token"


def test_blueprint_factory_with_permanent_token():
    reddit_bp = make_reddit_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="identity",
        redirect_to="index",
        permanent=True
    )
    assert isinstance(reddit_bp, OAuth2ConsumerBlueprint)
    assert reddit_bp.session.scope == "identity"
    assert reddit_bp.session.base_url == "https://oauth.reddit.com/"
    assert reddit_bp.session.client_id == "foo"
    assert reddit_bp.client_secret == "bar"
    assert reddit_bp.authorization_url == "https://www.reddit.com/api/v1/authorize"
    assert reddit_bp.token_url == "https://www.reddit.com/api/v1/access_token"
    assert reddit_bp.authorization_url_params["duration"] == "permanent"


def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["REDDIT_OAUTH_CLIENT_ID"] = "foo"
    app.config["REDDIT_OAUTH_CLIENT_SECRET"] = "bar"
    reddit_bp = make_reddit_blueprint(redirect_to="index")
    app.register_blueprint(reddit_bp)

    resp = app.test_client().get("/reddit")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    reddit_bp1 = make_reddit_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(reddit_bp1)

    app2 = Flask(__name__)
    reddit_bp2 = make_reddit_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(reddit_bp2)

    # outside of a request context, referencing functions on the `reddit` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        reddit.get("https://google.com")

    # inside of a request context, `reddit` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        reddit.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        reddit.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
