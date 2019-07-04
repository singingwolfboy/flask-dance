from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.meetup import make_meetup_blueprint, meetup
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the Meetup provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_meetup_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory():
    meetup_bp = make_meetup_blueprint(key="foo", secret="bar")
    assert isinstance(meetup_bp, OAuth2ConsumerBlueprint)
    assert meetup_bp.session.scope == ["basic"]
    assert meetup_bp.session.base_url == "https://api.meetup.com/2/"
    assert meetup_bp.session.client_id == "foo"
    assert meetup_bp.client_secret == "bar"
    assert meetup_bp.authorization_url == "https://secure.meetup.com/oauth2/authorize"
    assert meetup_bp.token_url == "https://secure.meetup.com/oauth2/access"
    assert meetup_bp.token_url_params == {"include_client_id": True}


def test_load_from_config(make_app):
    app = make_app()
    app.config["MEETUP_OAUTH_CLIENT_ID"] = "foo"
    app.config["MEETUP_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/meetup")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


def test_blueprint_factory_scope():
    meetup_bp = make_meetup_blueprint(key="foo", secret="bar", scope="customscope")
    assert meetup_bp.session.scope == "customscope"


@responses.activate
def test_context_local(make_app):
    responses.add(responses.GET, "https://meetup.com")

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
