import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.fitbit import make_fitbit_blueprint, fitbit
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.storage import MemoryStorage


@pytest.fixture
def make_app():
    "A callable to create a Flask app with the Fitbit provider"

    def _make_app(*args, **kwargs):
        app = Flask(__name__)
        app.secret_key = "whatever"
        blueprint = make_fitbit_blueprint(*args, **kwargs)
        app.register_blueprint(blueprint)
        return app

    return _make_app


def test_blueprint_factory():
    fitbit_bp = make_fitbit_blueprint(
        client_id="foo", client_secret="bar", scope="user:email", redirect_to="index"
    )
    assert isinstance(fitbit_bp, OAuth2ConsumerBlueprint)
    assert fitbit_bp.session.scope == "user:email"
    assert fitbit_bp.session.base_url == "https://api.fitbit.com/"
    assert fitbit_bp.session.client_id == "foo"
    assert fitbit_bp.client_secret == "bar"
    assert fitbit_bp.authorization_url == "https://www.fitbit.com/oauth2/authorize"
    assert fitbit_bp.token_url == "https://api.fitbit.com/oauth2/token"


def test_load_from_config(make_app):
    app = make_app()
    app.config["FITBIT_OAUTH_CLIENT_ID"] = "foo"
    app.config["FITBIT_OAUTH_CLIENT_SECRET"] = "bar"

    resp = app.test_client().get("/fitbit")
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

    # outside of a request context, referencing functions on the `fitbit` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        fitbit.get("https://google.com")

    # inside of a request context, `fitbit` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        fitbit.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        fitbit.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"
