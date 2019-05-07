from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.gitlab import make_gitlab_blueprint, gitlab
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the GitLab provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_gitlab_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory_default():
    # Test with gitlab.com
    glbp = make_gitlab_blueprint(
        client_id="foo", client_secret="bar", scope="read_user", redirect_to="index"
    )
    assert isinstance(glbp, OAuth2ConsumerBlueprint)
    assert glbp.session.scope == "read_user"
    assert glbp.session.base_url == "https://gitlab.com/api/v4/"
    assert glbp.session.client_id == "foo"
    assert glbp.client_secret == "bar"
    assert glbp.authorization_url == "https://gitlab.com/oauth/authorize"
    assert glbp.token_url == "https://gitlab.com/oauth/token"


def test_blueprint_factory_custom():
    glbp = make_gitlab_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="read_user",
        redirect_to="index",
        hostname="git.example.com",
    )
    assert isinstance(glbp, OAuth2ConsumerBlueprint)
    assert glbp.session.scope == "read_user"
    assert glbp.session.base_url == "https://git.example.com/api/v4/"
    assert glbp.session.client_id == "foo"
    assert glbp.client_secret == "bar"
    assert glbp.authorization_url == "https://git.example.com/oauth/authorize"
    assert glbp.token_url == "https://git.example.com/oauth/token"


def test_load_from_config(make_app):
    app = make_app()
    app.config["GITLAB_OAUTH_CLIENT_ID"] = "foo"
    app.config["GITLAB_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/gitlab")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local(make_app):
    responses.add(responses.GET, "https://google.com")

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

    # outside of a request context, referencing functions on the `gitlab` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        gitlab.get("https://google.com")

    # inside of a request context, `gitlab` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        gitlab.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        gitlab.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
