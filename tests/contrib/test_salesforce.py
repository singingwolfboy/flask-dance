from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.salesforce import make_salesforce_blueprint, salesforce
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage
from six import string_types


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the Salesforce provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_salesforce_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory_default():
    salesforce_bp = make_salesforce_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="api",
        redirect_to="index",
    )
    assert isinstance(salesforce_bp, OAuth2ConsumerBlueprint)
    assert salesforce_bp.session.scope == "api"
    assert salesforce_bp.session.base_url == "https://login.salesforce.com/"
    assert salesforce_bp.session.client_id == "foo"
    assert salesforce_bp.client_secret == "bar"
    assert (
        salesforce_bp.authorization_url
        == "https://login.salesforce.com/services/oauth2/authorize"
    )
    assert (
        salesforce_bp.token_url == "https://login.salesforce.com/services/oauth2/token"
    )


def test_blueprint_factory_sandbox():
    salesforce_bp = make_salesforce_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="api",
        redirect_to="index",
        is_sandbox=True,
    )
    assert isinstance(salesforce_bp, OAuth2ConsumerBlueprint)
    assert salesforce_bp.session.scope == "api"
    assert salesforce_bp.session.base_url == "https://test.salesforce.com/"
    assert salesforce_bp.session.client_id == "foo"
    assert salesforce_bp.client_secret == "bar"
    assert (
        salesforce_bp.authorization_url
        == "https://test.salesforce.com/services/oauth2/authorize"
    )
    assert (
        salesforce_bp.token_url == "https://test.salesforce.com/services/oauth2/token"
    )


def test_blueprint_factory_custom():
    salesforce_bp = make_salesforce_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="api",
        redirect_to="index",
        hostname="example.my.salesforce.com",
    )
    assert isinstance(salesforce_bp, OAuth2ConsumerBlueprint)
    assert salesforce_bp.session.scope == "api"
    assert salesforce_bp.session.base_url == "https://example.my.salesforce.com/"
    assert salesforce_bp.session.client_id == "foo"
    assert salesforce_bp.client_secret == "bar"
    assert (
        salesforce_bp.authorization_url
        == "https://example.my.salesforce.com/services/oauth2/authorize"
    )
    assert (
        salesforce_bp.token_url
        == "https://example.my.salesforce.com/services/oauth2/token"
    )


def test_load_from_config(make_app):
    app = make_app(redirect_to="index")
    app.config["SALESFORCE_OAUTH_CLIENT_ID"] = "foo"
    app.config["SALESFORCE_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/salesforce")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


def test_blueprint_factory_scope():
    salesforce_bp = make_salesforce_blueprint(
        client_id="foo", client_secret="bar", scope="customscope"
    )
    assert salesforce_bp.session.scope == "customscope"


@responses.activate
def test_context_local(make_app):
    responses.add(responses.GET, "https://salesforce.com")

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

    # outside of a request context, referencing functions on the `salesforce`
    # object will raise an exception
    with pytest.raises(RuntimeError):
        salesforce.get("https://salesforce.com")

    # inside of a request context, `salesforce` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        salesforce.get("https://salesforce.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        salesforce.get("https://salesforce.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"


def app_redirect_location(app):
    with app.test_client() as client:
        resp = client.get(
            "/salesforce", base_url="https://a.b.c", follow_redirects=False
        )
    assert resp.status_code == 302
    return URLObject(resp.headers["Location"])


def test_default_redirect_params(make_app):
    app = make_app("foo", "bar")
    query_dict = app_redirect_location(app).query_dict
    assert isinstance(query_dict.pop("state"), string_types)
    assert query_dict == {
        "client_id": "foo",
        "redirect_uri": "https://a.b.c/salesforce/authorized",
        "response_type": "code",
    }


def test_consent(make_app):
    app = make_app("foo", "bar", reprompt_consent=True)
    assert app_redirect_location(app).query_dict["prompt"] == "consent"
