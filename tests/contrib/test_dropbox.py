from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.dropbox import make_dropbox_blueprint, dropbox
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage
from six import string_types


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the Dropbox provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_dropbox_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory():
    dropbox_bp = make_dropbox_blueprint(app_key="foo", app_secret="bar")
    assert isinstance(dropbox_bp, OAuth2ConsumerBlueprint)
    assert dropbox_bp.session.base_url == "https://api.dropbox.com/2/"
    assert dropbox_bp.session.client_id == "foo"
    assert dropbox_bp.client_secret == "bar"
    assert dropbox_bp.authorization_url == "https://www.dropbox.com/oauth2/authorize"
    assert dropbox_bp.token_url == "https://api.dropbox.com/oauth2/token"


def test_load_from_config(make_app):
    app = make_app()
    app.config["DROPBOX_OAUTH_CLIENT_ID"] = "foo"
    app.config["DROPBOX_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/dropbox")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local(make_app):
    responses.add(responses.GET, "https://dropbox.com")

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

    # outside of a request context, referencing functions on the `dropbox` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        dropbox.get("https://dropbox.com")

    # inside of a request context, `dropbox` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        dropbox.get("https://dropbox.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        dropbox.get("https://dropbox.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"


def app_redirect_location(app):
    with app.test_client() as client:
        resp = client.get("/dropbox", base_url="https://a.b.c", follow_redirects=False)
    assert resp.status_code == 302
    return URLObject(resp.headers["Location"])


def test_default_redirect_params(make_app):
    app = make_app("foo", "bar")
    query_dict = app_redirect_location(app).query_dict
    assert isinstance(query_dict.pop("state"), string_types)
    assert query_dict == {
        "client_id": "foo",
        "redirect_uri": "https://a.b.c/dropbox/authorized",
        "response_type": "code",
    }


def test_force_reapprove(make_app):
    app = make_app("foo", "bar", force_reapprove=True)
    assert app_redirect_location(app).query_dict["force_reapprove"] == "true"


def test_disable_signup(make_app):
    app = make_app("foo", "bar", disable_signup=True)
    assert app_redirect_location(app).query_dict["disable_signup"] == "true"


def test_require_role(make_app):
    app = make_app("foo", "bar", require_role="work")
    assert app_redirect_location(app).query_dict["require_role"] == "work"


def test_offline(make_app):
    app = make_app("foo", "bar", offline=True)
    assert app_redirect_location(app).query_dict["token_access_type"] == "offline"
