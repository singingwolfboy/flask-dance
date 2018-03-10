from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.gitlab import make_gitlab_blueprint, gitlab
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend


def test_blueprint_factory():
    gitlab_bp = make_gitlab_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="read_user",
        redirect_to="index",
    )
    assert isinstance(gitlab_bp, OAuth2ConsumerBlueprint)
    assert gitlab_bp.session.scope == "read_user"
    assert gitlab_bp.session.base_url == "https://gitlab.com/api/v4/"
    assert gitlab_bp.session.client_id == "foo"
    assert gitlab_bp.client_secret == "bar"
    assert gitlab_bp.authorization_url == "https://gitlab.com/oauth/authorize"
    assert gitlab_bp.token_url == "https://gitlab.com/oauth/token"


def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["GITLAB_OAUTH_CLIENT_ID"] = "foo"
    app.config["GITLAB_OAUTH_CLIENT_SECRET"] = "bar"
    gitlab_bp = make_gitlab_blueprint(redirect_to="index")
    app.register_blueprint(gitlab_bp)

    resp = app.test_client().get("/gitlab")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    glbp1 = make_gitlab_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(glbp1)

    app2 = Flask(__name__)
    glbp2 = make_gitlab_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(glbp2)

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
