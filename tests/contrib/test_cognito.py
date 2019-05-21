from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.cognito import make_cognito_blueprint, cognito
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the GitLab provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_cognito_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory_default():
    # Test with gitlab.com
    cognitobp = make_cognito_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="read_user",
        redirect_to="index",
        cognito_domain_suffix="example",
    )
    assert isinstance(cognitobp, OAuth2ConsumerBlueprint)
    assert cognitobp.session.scope == "read_user"
    assert (
        cognitobp.session.base_url == "https://example.auth.eu-west-1.amazoncognito.com"
    )
    assert cognitobp.session.client_id == "foo"
    assert cognitobp.client_secret == "bar"
    assert (
        cognitobp.authorization_url
        == "https://example.auth.eu-west-1.amazoncognito.com/oauth2/authorize"
    )
    assert (
        cognitobp.token_url
        == "https://example.auth.eu-west-1.amazoncognito.com/oauth2/token"
    )


def test_blueprint_factory_custom():
    cognitobp = make_cognito_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="read_user",
        redirect_to="index",
        cognito_domain_suffix="example2",
    )
    assert isinstance(cognitobp, OAuth2ConsumerBlueprint)
    assert cognitobp.session.scope == "read_user"
    assert (
        cognitobp.session.base_url
        == "https://example2.auth.eu-west-1.amazoncognito.com"
    )
    assert cognitobp.session.client_id == "foo"
    assert cognitobp.client_secret == "bar"
    assert (
        cognitobp.authorization_url
        == "https://example2.auth.eu-west-1.amazoncognito.com/oauth2/authorize"
    )
    assert (
        cognitobp.token_url
        == "https://example2.auth.eu-west-1.amazoncognito.com/oauth2/token"
    )


def test_load_from_config(make_app):
    app = make_app()
    app.config["COGNITO_OAUTH_CLIENT_ID"] = "foo"
    app.config["COGNITO_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/cognito")
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
        cognito.get("https://google.com")

    # inside of a request context, `gitlab` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        cognito.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        cognito.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
