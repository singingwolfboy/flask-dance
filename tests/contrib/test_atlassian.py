from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.atlassian import make_atlassian_blueprint, atlassian
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage
from six import string_types


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the Atlassian provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_atlassian_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory():
    atlassian_bp = make_atlassian_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="read:jira-user",
        redirect_to="index",
    )
    assert isinstance(atlassian_bp, OAuth2ConsumerBlueprint)
    assert atlassian_bp.session.scope == "read:jira-user"
    assert atlassian_bp.session.base_url == "https://api.atlassian.com/"
    assert atlassian_bp.session.client_id == "foo"
    assert atlassian_bp.client_secret == "bar"
    assert atlassian_bp.authorization_url == "https://auth.atlassian.com/authorize"
    assert atlassian_bp.token_url == "https://auth.atlassian.com/oauth/token"


def test_load_from_config(make_app):
    app = make_app(redirect_to="index")
    app.config["ATLASSIAN_OAUTH_CLIENT_ID"] = "foo"
    app.config["ATLASSIAN_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/atlassian")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


def test_blueprint_factory_scope():
    atlassian_bp = make_atlassian_blueprint(
        client_id="foo", client_secret="bar", scope="customscope"
    )
    assert atlassian_bp.session.scope == "customscope"


@responses.activate
def test_context_local(make_app):
    responses.add(responses.GET, "https://atlassian.com")

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

    # outside of a request context, referencing functions on the `atlassian`
    # object will raise an exception
    with pytest.raises(RuntimeError):
        atlassian.get("https://atlassian.com")

    # inside of a request context, `atlassian` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        atlassian.get("https://atlassian.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        atlassian.get("https://atlassian.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"


def app_redirect_location(app):
    with app.test_client() as client:
        resp = client.get(
            "/atlassian", base_url="https://a.b.c", follow_redirects=False
        )
    assert resp.status_code == 302
    return URLObject(resp.headers["Location"])


def test_default_redirect_params(make_app):
    app = make_app("foo", "bar")
    query_dict = app_redirect_location(app).query_dict
    assert isinstance(query_dict.pop("state"), string_types)
    assert query_dict == {
        "audience": "api.atlassian.com",
        "client_id": "foo",
        "redirect_uri": "https://a.b.c/atlassian/authorized",
        "response_type": "code",
    }


def test_consent(make_app):
    app = make_app("foo", "bar", reprompt_consent=True)
    assert app_redirect_location(app).query_dict["prompt"] == "consent"
