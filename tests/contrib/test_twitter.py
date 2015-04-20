from __future__ import unicode_literals

import pytest
import mock
import responses
from flask import Flask
from flask_dance.contrib.twitter import make_twitter_blueprint, twitter
from flask_dance.consumer import OAuth1ConsumerBlueprint
from oauthlib.oauth1.rfc5849.utils import parse_authorization_header


def test_blueprint_factory():
    twitter_bp = make_twitter_blueprint(
        api_key="foobar",
        api_secret="supersecret",
        redirect_to="index",
    )
    assert isinstance(twitter_bp, OAuth1ConsumerBlueprint)
    assert twitter_bp.session.base_url == "https://api.twitter.com/1.1/"
    assert twitter_bp.session.auth.client.client_key == "foobar"
    assert twitter_bp.session.auth.client.client_secret == "supersecret"
    assert twitter_bp.request_token_url == "https://api.twitter.com/oauth/request_token"
    assert twitter_bp.access_token_url == "https://api.twitter.com/oauth/access_token"
    assert twitter_bp.authorization_url == "https://api.twitter.com/oauth/authorize"


@responses.activate
def test_load_from_config():
    responses.add(
        responses.POST,
        "https://api.twitter.com/oauth/request_token",
        body="oauth_token=faketoken&oauth_token_secret=fakesecret",
    )
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["TWITTER_OAUTH_API_KEY"] = "foo"
    app.config["TWITTER_OAUTH_API_SECRET"] = "bar"
    twitter_bp = make_twitter_blueprint(redirect_to="index")
    app.register_blueprint(twitter_bp)

    app.test_client().get("/twitter")
    auth_header = dict(parse_authorization_header(
        responses.calls[0].request.headers['Authorization'].decode('utf-8')
    ))
    assert auth_header["oauth_consumer_key"] == "foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://google.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    tbp1 = make_twitter_blueprint("foo1", "bar1", redirect_to="url1")
    app1.register_blueprint(tbp1)
    #tbp1.session.auth.client.get_oauth_signature = mock.Mock(return_value="sig1")

    app2 = Flask(__name__)
    tbp2 = make_twitter_blueprint("foo2", "bar2", redirect_to="url2")
    app2.register_blueprint(tbp2)
    #tbp2.session.auth.client.get_oauth_signature = mock.Mock(return_value="sig2")


    # outside of a request context, referencing functions on the `twitter` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        twitter.get("https://google.com")

    # inside of a request context, `twitter` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        tbp1.session.auth.client.get_oauth_signature = mock.Mock(return_value="sig1")
        tbp2.session.auth.client.get_oauth_signature = mock.Mock(return_value="sig2")

        app1.preprocess_request()
        twitter.get("https://google.com")
        auth_header = dict(parse_authorization_header(
            responses.calls[0].request.headers['Authorization'].decode('utf-8')
        ))
        assert auth_header["oauth_consumer_key"] == "foo1"
        assert auth_header["oauth_signature"] == "sig1"

    with app2.test_request_context("/"):
        tbp1.session.auth.client.get_oauth_signature = mock.Mock(return_value="sig1")
        tbp2.session.auth.client.get_oauth_signature = mock.Mock(return_value="sig2")

        app2.preprocess_request()
        twitter.get("https://google.com")
        auth_header = dict(parse_authorization_header(
            responses.calls[1].request.headers['Authorization'].decode('utf-8')
        ))
        assert auth_header["oauth_consumer_key"] == "foo2"
        assert auth_header["oauth_signature"] == "sig2"
