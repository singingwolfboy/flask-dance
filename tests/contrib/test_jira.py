from __future__ import unicode_literals

import pytest
import mock
import os
import tempfile
import responses
from flask import Flask
from flask_dance.contrib.jira import make_jira_blueprint, jira
from flask_dance.consumer import OAuth1ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend
from oauthlib.oauth1.rfc5849.utils import parse_authorization_header


def test_blueprint_factory():
    jira_bp = make_jira_blueprint(
        consumer_key="foobar",
        rsa_key="supersecret",
        base_url="https://flask.atlassian.net",
        redirect_to="index",
    )
    assert isinstance(jira_bp, OAuth1ConsumerBlueprint)
    assert jira_bp.session.base_url == "https://flask.atlassian.net"
    assert jira_bp.session.auth.client.client_key == "foobar"
    assert jira_bp.session.auth.client.rsa_key == "supersecret"
    assert jira_bp.request_token_url == "https://flask.atlassian.net/plugins/servlet/oauth/request-token"
    assert jira_bp.access_token_url == "https://flask.atlassian.net/plugins/servlet/oauth/access-token"
    assert jira_bp.authorization_url == "https://flask.atlassian.net/plugins/servlet/oauth/authorize"


def test_rsa_key_file():
    key_fd, key_file_path = tempfile.mkstemp()
    with os.fdopen(key_fd, 'w') as key_file:
        key_file.write("my-fake-key")

    jira_bp = make_jira_blueprint(
        rsa_key=key_file_path,
        base_url="https://flask.atlassian.net",
    )
    assert jira_bp.rsa_key == "my-fake-key"

    os.remove(key_file_path)


@responses.activate
@mock.patch("oauthlib.oauth1.rfc5849.signature.sign_rsa_sha1", return_value="fakesig")
def test_load_from_config(sign_func):
    responses.add(
        responses.POST,
        "https://flask.atlassian.net/plugins/servlet/oauth/request-token",
        body="oauth_token=faketoken&oauth_token_secret=fakesecret",
    )
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["JIRA_OAUTH_CONSUMER_KEY"] = "foo"
    app.config["JIRA_OAUTH_RSA_KEY"] = "bar"
    jira_bp = make_jira_blueprint("https://flask.atlassian.net", redirect_to="index")
    app.register_blueprint(jira_bp)

    resp = app.test_client().get("/jira")
    auth_header = dict(parse_authorization_header(
        responses.calls[0].request.headers['Authorization'].decode('utf-8')
    ))
    assert auth_header["oauth_consumer_key"] == "foo"
    assert sign_func.call_args[0][1] == "bar"


@responses.activate
@mock.patch("oauthlib.oauth1.rfc5849.signature.sign_rsa_sha1", return_value="fakesig")
def test_content_type(sign_func):
    responses.add(responses.GET, "https://flask.atlassian.net/")

    app = Flask(__name__)
    app.secret_key = "anything"
    app.debug = True
    backend = MemoryBackend({
        "oauth_token": "faketoken",
        "oauth_token_secret": "fakesecret",
        "oauth_session_handle": "fakehandle",
        "oauth_expires_in": "157680000",
        "oauth_authorization_expires_in": "160272000",
    })
    jira_bp = make_jira_blueprint(
        "https://flask.atlassian.net",
        rsa_key="fakersa",
        consumer_key="fakekey",
        backend=backend,
    )
    app.register_blueprint(jira_bp)

    @app.route("/test")
    def api_request():
        jira_bp.session.get("/")
        return "success"

    resp = app.test_client().get("/test")
    headers = responses.calls[0].request.headers
    assert "Content-Type" in headers
    assert headers["Content-Type"] == "application/json".encode('utf-8')


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    jbp1 = make_jira_blueprint("https://t1.atlassian.com", "foo1", "bar1", redirect_to="url1")
    app1.register_blueprint(jbp1)

    app2 = Flask(__name__)
    jbp2 = make_jira_blueprint("https://t2.atlassian.com", "foo2", "bar2", redirect_to="url2")
    app2.register_blueprint(jbp2)


    # outside of a request context, referencing functions on the `jira` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        jira.get("https://google.com")

    # inside of a request context, `jira` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        jbp1.session.auth.client.get_oauth_signature = mock.Mock(return_value="sig1")
        jbp2.session.auth.client.get_oauth_signature = mock.Mock(return_value="sig2")

        app1.preprocess_request()
        jira.get("https://google.com")
        auth_header = dict(parse_authorization_header(
            responses.calls[0].request.headers['Authorization'].decode('utf-8')
        ))
        assert auth_header["oauth_consumer_key"] == "foo1"
        assert auth_header["oauth_signature"] == "sig1"

    with app2.test_request_context("/"):
        jbp1.session.auth.client.get_oauth_signature = mock.Mock(return_value="sig1")
        jbp2.session.auth.client.get_oauth_signature = mock.Mock(return_value="sig2")

        app2.preprocess_request()
        jira.get("https://google.com")
        auth_header = dict(parse_authorization_header(
            responses.calls[1].request.headers['Authorization'].decode('utf-8')
        ))
        assert auth_header["oauth_consumer_key"] == "foo2"
        assert auth_header["oauth_signature"] == "sig2"
