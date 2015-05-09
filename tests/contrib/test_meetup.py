from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.meetup import make_meetup_blueprint, meetup
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend


def test_blueprint_factory():
    meetup_bp = make_meetup_blueprint(
        key="foo",
        secret="bar",
    )
    assert isinstance(meetup_bp, OAuth2ConsumerBlueprint)
    assert meetup_bp.session.scope == ["basic"]
    assert meetup_bp.session.base_url == "https://api.meetup.com/2/"
    assert meetup_bp.session.client_id == "foo"
    assert meetup_bp.client_secret == "bar"
    assert meetup_bp.authorization_url == "https://secure.meetup.com/oauth2/authorize"
    assert meetup_bp.token_url == "https://secure.meetup.com/oauth2/access"


def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["MEETUP_OAUTH_KEY"] = "foo"
    app.config["MEETUP_OAUTH_SECRET"] = "bar"
    meetup_bp = make_meetup_blueprint()
    app.register_blueprint(meetup_bp)

    resp = app.test_client().get("/meetup")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


def test_blueprint_factory_scope():
    meetup_bp = make_meetup_blueprint(
        key="foo", secret="bar",
        scope="customscope",
    )
    assert meetup_bp.session.scope == "customscope"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://meetup.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    meetup_bp1 = make_meetup_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(meetup_bp1)

    app2 = Flask(__name__)
    meetup_bp2 = make_meetup_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(meetup_bp2)

    # outside of a request context, referencing functions on the `meetup` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        meetup.get("https://meetup.com")

    # inside of a request context, `meetup` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        meetup.get("https://meetup.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        meetup.get("https://meetup.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
