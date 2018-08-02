from __future__ import unicode_literals

import pytest
import responses
from flask import Flask
from urlobject import URLObject

from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend
from flask_dance.contrib.azure import make_azure_blueprint, azure


def test_blueprint_factory():
    azure_bp = make_azure_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="user.read",
        redirect_to="index",
    )
    assert isinstance(azure_bp, OAuth2ConsumerBlueprint)
    assert azure_bp.session.scope == "user.read"
    assert azure_bp.session.base_url == "https://graph.microsoft.com"
    assert azure_bp.session.client_id == "foo"
    assert azure_bp.client_secret == "bar"
    assert azure_bp.authorization_url == "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    assert azure_bp.token_url == "https://login.microsoftonline.com/common/oauth2/v2.0/token"


def test_blueprint_factory_with_organization_tenant():
    azure_orgs_bp = make_azure_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="user.read",
        redirect_to="index",
        tenant='organizations'
    )
    assert isinstance(azure_orgs_bp, OAuth2ConsumerBlueprint)
    assert azure_orgs_bp.session.scope == "user.read"
    assert azure_orgs_bp.session.base_url == "https://graph.microsoft.com"
    assert azure_orgs_bp.session.client_id == "foo"
    assert azure_orgs_bp.client_secret == "bar"
    assert azure_orgs_bp.authorization_url == "https://login.microsoftonline.com/organizations/oauth2/v2.0/authorize"
    assert azure_orgs_bp.token_url == "https://login.microsoftonline.com/organizations/oauth2/v2.0/token"


def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["AZURE_OAUTH_CLIENT_ID"] = "foo"
    app.config["AZURE_OAUTH_CLIENT_SECRET"] = "bar"
    azure_bp = make_azure_blueprint(redirect_to="index")
    app.register_blueprint(azure_bp)

    resp = app.test_client().get("/azure")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    ghbp1 = make_azure_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(ghbp1)

    app2 = Flask(__name__)
    ghbp2 = make_azure_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(ghbp2)

    # outside of a request context, referencing functions on the `azure` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        azure.get("https://google.com")

    # inside of a request context, `azure` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        azure.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        azure.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
