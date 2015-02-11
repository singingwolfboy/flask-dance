from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import OAuth2ConsumerBlueprint


def test_blueprint_factory():
    google_bp = make_google_blueprint(
        client_id="foo",
        client_secret="bar",
        redirect_to="index",
    )
    assert isinstance(google_bp, OAuth2ConsumerBlueprint)
    assert google_bp.session.scope == ["profile"]
    assert google_bp.session.base_url == "https://www.googleapis.com/"
    assert google_bp.session.client_id == "foo"
    assert google_bp.client_secret == "bar"
    assert google_bp.authorization_url == "https://accounts.google.com/o/oauth2/auth"
    assert google_bp.token_url == "https://accounts.google.com/o/oauth2/token"


@pytest.mark.xfail  # remove when https://github.com/requests/requests-oauthlib/pull/172 is released
def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["GOOGLE_OAUTH_CLIENT_ID"] = "foo"
    app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = "bar"
    google_bp = make_google_blueprint(redirect_to="index")
    app.register_blueprint(google_bp)

    resp = app.test_client().get("/google")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


def test_blueprint_factory_scope():
    google_bp = make_google_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="customscope",
        redirect_to="index",
    )
    assert google_bp.session.scope == "customscope"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    goog_bp1 = make_google_blueprint("foo1", "bar1", redirect_to="url1")
    app1.register_blueprint(goog_bp1)
    goog_bp1.token_getter(lambda: {"access_token": "app1"})

    app2 = Flask(__name__)
    goog_bp2 = make_google_blueprint("foo2", "bar2", redirect_to="url2")
    app2.register_blueprint(goog_bp2)
    goog_bp2.token_getter(lambda: {"access_token": "app2"})

    # outside of a request context, referencing functions on the `google` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        google.get("https://github.com")

    # inside of a request context, `google` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        google.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        google.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
