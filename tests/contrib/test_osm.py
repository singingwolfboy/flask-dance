import pytest
import responses
from flask import Flask
from urlobject import URLObject

from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage
from flask_dance.contrib.osm import make_osm_blueprint, osm


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the GitHub provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_osm_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory():
    osm_bp = make_osm_blueprint(
        client_id="foo", client_secret="bar", scope="user:email", redirect_to="index"
    )
    assert isinstance(osm_bp, OAuth2ConsumerBlueprint)
    assert osm_bp.session.scope == "user:email"
    assert osm_bp.session.base_url == "https://www.openstreetmap.org/api/0.6/"
    assert osm_bp.session.client_id == "foo"
    assert osm_bp.client_secret == "bar"
    assert osm_bp.authorization_url == "https://www.openstreetmap.org/oauth2/authorize"
    assert osm_bp.token_url == "https://www.openstreetmap.org/oauth2/token"


def test_load_from_config(make_app):
    app = make_app()
    app.config["OSM_OAUTH_CLIENT_ID"] = "foo"
    app.config["OSM_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/osm")
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

    # outside of a request context, referencing functions on the `osm` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        osm.get("https://google.com")

    # inside of a request context, `osm` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        osm.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        osm.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
