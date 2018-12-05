from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from flask import Flask
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend


def test_blueprint_factory():
    facebook_bp = make_facebook_blueprint(
        client_id="foo",
        client_secret="bar",
        scope="user:email",
        redirect_to="index",
    )
    assert isinstance(facebook_bp, OAuth2ConsumerBlueprint)
    assert facebook_bp.session.scope == "user:email"
    assert facebook_bp.session.base_url == "https://graph.facebook.com/"
    assert facebook_bp.session.client_id == "foo"
    assert facebook_bp.client_secret == "bar"
    assert facebook_bp.authorization_url == "https://www.facebook.com/dialog/oauth"
    assert facebook_bp.token_url == "https://graph.facebook.com/oauth/access_token"


def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["FACEBOOK_OAUTH_CLIENT_ID"] = "foo"
    app.config["FACEBOOK_OAUTH_CLIENT_SECRET"] = "bar"
    facebook_bp = make_facebook_blueprint(redirect_to="index")
    app.register_blueprint(facebook_bp)

    resp = app.test_client().get("/facebook")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    fbbp1 = make_facebook_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(fbbp1)

    app2 = Flask(__name__)
    fbbp2 = make_facebook_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(fbbp2)

    # outside of a request context, referencing functions on the `facebook` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        facebook.get("https://google.com")

    # inside of a request context, `facebook` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        facebook.get("https://google.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        facebook.get("https://google.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"


@pytest.mark.parametrize("rerequest", (True, False))
def test_rerequest_declined_scopes(rerequest):
    """
    Tests that the rerequest_declined_permissions flag in the facebook blueprint sends
    toggles the header reasking oauth permissions as detailed in the facebook docs https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow#reaskperms

    Tests both that the header is set with the flag (rerequest=True) and that it is missing without the flag (rerequest=False)
    """
    app = Flask(__name__)
    app.secret_key = "backups"
    bp = make_facebook_blueprint(
        scope='user_posts', rerequest_declined_permissions=rerequest)
    app.register_blueprint(bp)
    with app.test_client() as client:
        resp = client.get(
            "/facebook",
            base_url="https://a.b.c",
            follow_redirects=False,
        )
    assert resp.status_code == 302
    location = URLObject(resp.headers["Location"])
    if rerequest:
        assert location.query_dict["auth_type"] == "rerequest"
    else:
        assert "auth_type" not in location.query_dict
