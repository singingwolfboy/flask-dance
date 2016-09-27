# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import json
import re
from oauthlib.oauth2 import MissingCodeError

try:
    from urllib.parse import quote_plus, parse_qsl
except ImportError:
    from urllib import quote_plus
    from urlparse import parse_qsl
import pytest
import mock
import responses
from urlobject import URLObject
import flask
from freezegun import freeze_time
from werkzeug.contrib.fixers import ProxyFix
from flask_dance.consumer import (
    OAuth2ConsumerBlueprint, oauth_authorized, oauth_error
)
from flask_dance.consumer.requests import OAuth2Session

try:
    import blinker
except ImportError:
    blinker = None
requires_blinker = pytest.mark.skipif(not blinker, reason="requires blinker")


def make_app(login_url=None, debug=False):
    blueprint = OAuth2ConsumerBlueprint("test-service", __name__,
        client_id="client_id",
        client_secret="client_secret",
        scope="admin",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_to="index",
        login_url=login_url,
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")
    app.debug = debug

    @app.route("/")
    def index():
        return "index"

    return app, blueprint

def test_generate_login_url():
    app, _ = make_app()
    with app.test_request_context("/"):
        login_url = flask.url_for("test-service.login")
        assert login_url == "/login/test-service"

def test_override_login_url():
    app, _ = make_app(login_url="/crazy/custom/url")
    with app.test_request_context("/"):
        login_url = flask.url_for("test-service.login")
        assert login_url == "/login/crazy/custom/url"


@responses.activate
def test_login_url():
    app, _ = make_app()
    with app.test_client() as client:
        resp = client.get(
            "/login/test-service",
            base_url="https://a.b.c",
            follow_redirects=False,
        )
        # check that we saved the state in the session
        assert flask.session["test-service_oauth_state"] == "random-string"
    # check that we redirected the client
    assert resp.status_code == 302
    location = URLObject(resp.headers["Location"])
    assert location.without_query() == "https://example.com/oauth/authorize"
    assert location.query_dict["client_id"] == "client_id"
    assert location.query_dict["redirect_uri"] == "https://a.b.c/login/test-service/authorized"
    assert location.query_dict["scope"] == "admin"
    assert location.query_dict["state"] == "random-string"


@responses.activate
def test_login_url_forwarded_proto():
    app, _ = make_app()
    app.wsgi_app = ProxyFix(app.wsgi_app)
    with app.test_client() as client:
        resp = client.get(
            "/login/test-service",
            base_url="http://a.b.c",
            headers={"X-Forwarded-Proto": "https"},
            follow_redirects=False,
        )
    # check that we redirected the client with a https redirect_uri
    assert resp.status_code == 302
    location = URLObject(resp.headers["Location"])
    assert location.query_dict["redirect_uri"] == "https://a.b.c/login/test-service/authorized"


@responses.activate
def test_authorized_url():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":"admin"}',
    )
    app, _ = make_app()
    with app.test_client() as client:
        # reset the session before the request
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"
        # make the request
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
            base_url="https://a.b.c",
        )
        # check that we redirected the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://a.b.c/"
        # check that we obtained an access token
        assert len(responses.calls) == 1
        request_data = dict(parse_qsl(responses.calls[0].request.body))
        assert request_data["client_id"] == "client_id"
        assert request_data["redirect_uri"] == "https://a.b.c/login/test-service/authorized"
        # check that we stored the access token in the session
        assert (
            flask.session["test-service_oauth_token"] ==
            {'access_token': 'foobar', 'scope': ['admin'], 'token_type': 'bearer'}
        )


def test_authorized_url_no_state():
    app, _ = make_app()
    with app.test_client() as client:
        # make the request, without resetting the session beforehand
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
            base_url="https://a.b.c",
        )
        # check that we redirected the client back to login view
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://a.b.c/login/test-service"
        # check that there's nothing in the session
        assert "test-service_oauth_token" not in flask.session


@responses.activate
def test_authorized_url_behind_proxy():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":"admin"}',
    )
    app, _ = make_app()
    app.wsgi_app = ProxyFix(app.wsgi_app)
    with app.test_client() as client:
        # reset the session before the request
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"
        # make the request
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
            base_url="http://a.b.c",
            headers={"X-Forwarded-Proto": "https"},
        )
        request_data = dict(parse_qsl(responses.calls[0].request.body))
        # this should be https
        assert request_data["redirect_uri"] == "https://a.b.c/login/test-service/authorized"


def test_authorized_url_invalid_response():
    app, _ = make_app(debug=True)
    with app.test_client() as client:
        # reset the session before the request
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"
        # make the request
        with pytest.raises(MissingCodeError) as missingError:
            client.get(
                "/login/test-service/authorized?error_code=1349048&error_message=IMUSEFUL",
                base_url="https://a.b.c",
            )
        match = re.search(r"{[^}]*}", str(missingError.value))
        err_dict = json.loads(match.group(0))
        assert err_dict == {"error_message": "IMUSEFUL", "error_code": "1349048"}


@responses.activate
@freeze_time("2016-01-01 12:00:01")
def test_authorized_url_token_lifetime():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","expires_in":300}',
    )
    app, _ = make_app()

    with app.test_client() as client:
        # reset the session before the request
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"
        # make the request
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
            base_url="https://a.b.c",
        )
        # check that we redirected the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://a.b.c/"
        # check that we obtained an access token
        assert len(responses.calls) == 1
        request_data = dict(parse_qsl(responses.calls[0].request.body))
        assert request_data["client_id"] == "client_id"
        assert request_data["redirect_uri"] == "https://a.b.c/login/test-service/authorized"
        # check that we stored the access token and expiration date in the session
        expected_stored_token = {
            'access_token': 'foobar',
            'token_type': 'bearer',
            'expires_in': 300,
            'expires_at': 1451649901,
        }
        assert flask.session["test-service_oauth_token"] == expected_stored_token


def test_return_expired_token(request):
    app, bp = make_app()
    time1 = "2016-01-01 12:00:01"
    time2 = "2016-01-01 12:05:00"  # 299 sec in future
    time3 = "2016-01-01 12:10:01"  # 600 sec in future
    token = {
        'access_token': 'foobar',
        'token_type': 'bearer',
        'expires_in': 300,  # expires in 300 seconds
    }
    ctx = app.test_request_context('/')
    request.addfinalizer(ctx.pop)
    ctx.push()

    with freeze_time(time1):
        bp.token = token
        modified1 = token.copy()
        modified1["expires_at"] = 1451649901
        assert bp.token == modified1

    with freeze_time(time2):
        modified2 = token.copy()
        modified2["expires_in"] = 1
        modified2["expires_at"] = 1451649901
        assert bp.token == modified2

    with freeze_time(time3):
        modified3 = token.copy()
        modified3["expires_in"] = -300
        modified3["expires_at"] = 1451649901
        assert bp.token == modified3


@responses.activate
def test_provider_error():
    app, _ = make_app()
    with app.test_client() as client:
        # make the request
        resp = client.get(
            "/login/test-service/authorized?"
            "error=invalid_redirect&"
            "error_description=Invalid+redirect_URI&"
            "error_uri=https%3a%2f%2fexample.com%2fdocs%2fhelp",
            base_url="https://a.b.c",
        )
        # even though there was an error, we should still redirect the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://a.b.c/"
        # shouldn't even try getting an access token, though
        assert len(responses.calls) == 0


@responses.activate
def test_redirect_url():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":"admin"}',
    )
    blueprint = OAuth2ConsumerBlueprint("test-service", __name__,
        client_id="client_id",
        client_secret="client_secret",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_url="http://mysite.cool/whoa?query=basketball",
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    with app.test_client() as client:
        # reset the session before the request
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"
        # make the request
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
            base_url="https://a.b.c",
        )
        # check that we redirected the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "http://mysite.cool/whoa?query=basketball"


@responses.activate
def test_redirect_to():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":"admin"}',
    )
    blueprint = OAuth2ConsumerBlueprint("test-service", __name__,
        client_id="client_id",
        client_secret="client_secret",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_to="my_view",
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/blargl")
    def my_view():
        return "check out my url"

    with app.test_client() as client:
        # reset the session before the request
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"
        # make the request
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
            base_url="https://a.b.c",
        )
        # check that we redirected the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://a.b.c/blargl"


@responses.activate
def test_redirect_fallback():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":"admin"}',
    )
    blueprint = OAuth2ConsumerBlueprint("test-service", __name__,
        client_id="client_id",
        client_secret="client_secret",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/blargl")
    def my_view():
        return "check out my url"

    with app.test_client() as client:
        # reset the session before the request
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"
        # make the request
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
            base_url="https://a.b.c",
        )
        # check that we redirected the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://a.b.c/"


@requires_blinker
def test_signal_oauth_authorized(request):
    app, bp = make_app()

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))

    oauth_authorized.connect(callback)
    request.addfinalizer(lambda: oauth_authorized.disconnect(callback))
    fake_token = {"access_token": "test-token"}

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"

        bp.session.fetch_token = mock.Mock(return_value=fake_token)
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
        )
        assert resp.status_code == 302
        # check that we stored the token
        assert flask.session["test-service_oauth_token"] == fake_token

    assert len(calls) == 1
    assert calls[0][0] == (bp,)
    assert calls[0][1] == {"token": fake_token}


@requires_blinker
def test_signal_oauth_authorized_abort(request):
    app, bp = make_app()

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))
        return False

    oauth_authorized.connect(callback)
    request.addfinalizer(lambda: oauth_authorized.disconnect(callback))
    fake_token = {"access_token": "test-token"}

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"

        bp.session.fetch_token = mock.Mock(return_value=fake_token)

        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
        )
        # check that we did NOT store the token
        assert "test-service_oauth_token" not in flask.session

    # callback still should have been called
    assert len(calls) == 1


@requires_blinker
def test_signal_oauth_authorized_response(request):
    app, bp = make_app()

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))
        return flask.redirect("/url")

    oauth_authorized.connect(callback)
    request.addfinalizer(lambda: oauth_authorized.disconnect(callback))
    fake_token = {"access_token": "test-token"}

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"

        bp.session.fetch_token = mock.Mock(return_value=fake_token)

        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "http://localhost/url"
        # check that we did NOT store the token
        assert "test-service_oauth_token" not in flask.session

    # callback still should have been called
    assert len(calls) == 1


@requires_blinker
def test_signal_sender_oauth_authorized(request):
    app, bp = make_app()
    bp2 = OAuth2ConsumerBlueprint("test2", __name__,
        client_id="client_id",
        client_secret="client_secret",
        scope="admin",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_to="index",
    )
    app.register_blueprint(bp2, url_prefix="/login")

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))

    oauth_authorized.connect(callback, sender=bp)
    request.addfinalizer(lambda: oauth_authorized.disconnect(callback, sender=bp))
    fake_token = {"access_token": "test-token"}
    fake_token2 = {"access_token": "test-token2"}

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"

        bp.session.fetch_token = mock.Mock(return_value=fake_token)
        bp2.session.fetch_token = mock.Mock(return_value=fake_token2)

        resp = client.get(
            "/login/test2/authorized?code=secret-code&state=random-string",
        )

    assert len(calls) == 0

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"

        bp.session.fetch_token = mock.Mock(return_value="test-token")
        bp2.session.fetch_token = mock.Mock(return_value="test2-token")

        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
        )

    assert len(calls) == 1
    assert calls[0][0] == (bp,)
    assert calls[0][1] == {"token": "test-token"}

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"

        bp.session.fetch_token = mock.Mock(return_value=fake_token)
        bp2.session.fetch_token = mock.Mock(return_value=fake_token2)

        resp = client.get(
            "/login/test2/authorized?code=secret-code&state=random-string",
        )

    assert len(calls) == 1  # unchanged


@requires_blinker
def test_signal_oauth_error(request):
    app, bp = make_app()

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))

    oauth_error.connect(callback)
    request.addfinalizer(lambda: oauth_error.disconnect(callback))

    with app.test_client() as client:
        resp = client.get(
            "/login/test-service/authorized?"
            "error=unauthorized_client&"
            "error_description=Invalid+redirect+URI&"
            "error_uri=https%3a%2f%2fexample.com%2fdocs%2fhelp",
            base_url="https://a.b.c",
        )

    assert len(calls) == 1
    assert calls[0][0] == (bp,)
    assert calls[0][1] == {
        "error": "unauthorized_client",
        "error_description": "Invalid redirect URI",
        "error_uri": "https://example.com/docs/help",
    }
    assert resp.status_code == 302


class CustomOAuth2Session(OAuth2Session):
    my_attr = "foobar"


def test_custom_session_class():
    bp = OAuth2ConsumerBlueprint("test", __name__,
        client_id="client_id",
        client_secret="client_secret",
        scope="admin",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_to="index",
        session_class=CustomOAuth2Session,
    )
    assert isinstance(bp.session, CustomOAuth2Session)
    assert bp.session.my_attr == "foobar"
