from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.dropbox import make_dropbox_blueprint, dropbox
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend


def test_blueprint_factory():
    dropbox_bp = make_dropbox_blueprint(
        app_key="foo",
        app_secret="bar",
    )
    assert isinstance(dropbox_bp, OAuth2ConsumerBlueprint)
    assert dropbox_bp.session.base_url == "https://api.dropbox.com/1/"
    assert dropbox_bp.session.client_id == "foo"
    assert dropbox_bp.client_secret == "bar"
    assert dropbox_bp.authorization_url == "https://www.dropbox.com/1/oauth2/authorize"
    assert dropbox_bp.token_url == "https://api.dropbox.com/1/oauth2/token"


def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["DROPBOX_OAUTH_APP_KEY"] = "foo"
    app.config["DROPBOX_OAUTH_APP_SECRET"] = "bar"
    dropbox_bp = make_dropbox_blueprint()
    app.register_blueprint(dropbox_bp)

    resp = app.test_client().get("/dropbox")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://dropbox.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    dropbox_bp1 = make_dropbox_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(dropbox_bp1)

    app2 = Flask(__name__)
    dropbox_bp2 = make_dropbox_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(dropbox_bp2)

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


def test_force_reapprove():
    app = Flask(__name__)
    app.secret_key = "forced"
    dropbox_bp = make_dropbox_blueprint("foo", "bar", force_reapprove=True)
    app.register_blueprint(dropbox_bp)

    with app.test_client() as client:
        resp = client.get(
            "/dropbox",
            base_url="https://a.b.c",
            follow_redirects=False,
        )
    # check that there is a `force_reapprove=true` query param in the redirect URL
    assert resp.status_code == 302
    location = URLObject(resp.headers["Location"])
    assert location.query_dict["force_reapprove"] == "true"


def test_disable_signup():
    app = Flask(__name__)
    app.secret_key = "apple-app-store"
    dropbox_bp = make_dropbox_blueprint(
        "foo", "bar", disable_signup=True,
    )
    app.register_blueprint(dropbox_bp)

    with app.test_client() as client:
        resp = client.get(
            "/dropbox",
            base_url="https://a.b.c",
            follow_redirects=False,
        )
    assert resp.status_code == 302
    location = URLObject(resp.headers["Location"])
    assert location.query_dict["disable_signup"] == "true"
