from __future__ import unicode_literals

import pytest
import responses
from urlobject import URLObject
from werkzeug.urls import url_decode
from flask import Flask
from flask_dance.contrib.slack import make_slack_blueprint, slack
from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.backend import MemoryBackend

import requests_oauthlib
requires_overridable_fixer = pytest.mark.skipif(
    requests_oauthlib.__version__ <= '0.6.0',
    reason="requires an overridable Slack fixer",
)


def test_blueprint_factory():
    slack_bp = make_slack_blueprint(
        client_id="foo",
        client_secret="bar",
        scope=["identity", "im:write"],
        redirect_to="index",
    )
    assert isinstance(slack_bp, OAuth2ConsumerBlueprint)
    assert slack_bp.session.scope == ["identity", "im:write"]
    assert slack_bp.session.base_url == "https://slack.com/api/"
    assert slack_bp.session.client_id == "foo"
    assert slack_bp.client_secret == "bar"
    assert slack_bp.authorization_url == "https://slack.com/oauth/authorize"
    assert slack_bp.token_url == "https://slack.com/api/oauth.access"


def test_load_from_config():
    app = Flask(__name__)
    app.secret_key = "anything"
    app.config["SLACK_OAUTH_CLIENT_ID"] = "foo"
    app.config["SLACK_OAUTH_CLIENT_SECRET"] = "bar"
    slack_bp = make_slack_blueprint(redirect_to="index")
    app.register_blueprint(slack_bp)

    resp = app.test_client().get("/slack")
    url = resp.headers["Location"]
    client_id = URLObject(url).query.dict.get("client_id")
    assert client_id == "foo"


@responses.activate
def test_context_local():
    responses.add(responses.GET, "https://slack.com")

    # set up two apps with two different set of auth tokens
    app1 = Flask(__name__)
    sbp1 = make_slack_blueprint(
        "foo1", "bar1", redirect_to="url1",
        backend=MemoryBackend({"access_token": "app1"}),
    )
    app1.register_blueprint(sbp1)

    app2 = Flask(__name__)
    sbp2 = make_slack_blueprint(
        "foo2", "bar2", redirect_to="url2",
        backend=MemoryBackend({"access_token": "app2"}),
    )
    app2.register_blueprint(sbp2)

    # outside of a request context, referencing functions on the `slack` object
    # will raise an exception
    with pytest.raises(RuntimeError):
        slack.get("https://slack.com")

    # inside of a request context, `slack` should be a proxy to the correct
    # blueprint session
    with app1.test_request_context("/"):
        app1.preprocess_request()
        slack.get("https://slack.com")
        request = responses.calls[0].request
        assert request.headers["Authorization"] == "Bearer app1"

    with app2.test_request_context("/"):
        app2.preprocess_request()
        slack.get("https://slack.com")
        request = responses.calls[1].request
        assert request.headers["Authorization"] == "Bearer app2"


@requires_overridable_fixer
@responses.activate
def test_auto_token_get():
    responses.add(responses.GET, "https://slack.com/api/chat.postMessage")

    app = Flask(__name__)
    slack_bp = make_slack_blueprint(
        client_id="foo", client_secret="bar",
        backend=MemoryBackend({"access_token": "abcde"}),
    )
    app.register_blueprint(slack_bp, url_prefix="/login")

    with app.test_request_context("/"):
        app.preprocess_request()
        resp = slack.get("chat.postMessage", data={
            "channel": "#general",
            "text": "ping",
            "icon_emoji": ":robot_face:",
        })
    request_data = url_decode(resp.request.body)
    assert request_data["channel"] == "#general"
    assert request_data["text"] == "ping"
    assert request_data["icon_emoji"] == ":robot_face:"
    # the `token` parameter should have been automatically added
    assert request_data["token"] == "abcde"


@requires_overridable_fixer
@responses.activate
def test_auto_token_post():
    responses.add(responses.POST, "https://slack.com/api/chat.postMessage")

    app = Flask(__name__)
    slack_bp = make_slack_blueprint(
        client_id="foo", client_secret="bar",
        backend=MemoryBackend({"access_token": "abcde"}),
    )
    app.register_blueprint(slack_bp, url_prefix="/login")

    with app.test_request_context("/"):
        app.preprocess_request()
        resp = slack.post("chat.postMessage", data={
            "channel": "#general",
            "text": "ping",
            "icon_emoji": ":robot_face:",
        })
    request_data = url_decode(resp.request.body)
    assert request_data["channel"] == "#general"
    assert request_data["text"] == "ping"
    assert request_data["icon_emoji"] == ":robot_face:"
    # the `token` parameter should have been automatically added
    assert request_data["token"] == "abcde"


@responses.activate
def test_auto_token_post_no_token():
    responses.add(responses.POST, "https://slack.com/api/chat.postMessage")

    app = Flask(__name__)
    slack_bp = make_slack_blueprint(
        client_id="foo", client_secret="bar",
    )
    app.register_blueprint(slack_bp, url_prefix="/login")

    with app.test_request_context("/"):
        app.preprocess_request()
        resp = slack.post("chat.postMessage", data={
            "channel": "#general",
            "text": "ping",
            "icon_emoji": ":robot_face:",
        })
    request_data = url_decode(resp.request.body)
    assert request_data["channel"] == "#general"
    assert request_data["text"] == "ping"
    assert request_data["icon_emoji"] == ":robot_face:"
    assert "token" not in request_data
    url = URLObject(resp.request.url)
    assert "token" not in url.query_dict


@requires_overridable_fixer
@responses.activate
def test_override_token_get():
    responses.add(responses.GET, "https://slack.com/api/chat.postMessage")

    app = Flask(__name__)
    slack_bp = make_slack_blueprint(
        client_id="foo", client_secret="bar",
        backend=MemoryBackend({"access_token": "abcde"}),
    )
    app.register_blueprint(slack_bp, url_prefix="/login")

    with app.test_request_context("/"):
        app.preprocess_request()
        resp = slack.get("chat.postMessage", data={
            "token": "xyz",
            "channel": "#general",
            "text": "ping",
            "icon_emoji": ":robot_face:",
        })
    request_data = url_decode(resp.request.body)
    assert request_data["token"] == "xyz"
    assert request_data["channel"] == "#general"
    assert request_data["text"] == "ping"
    assert request_data["icon_emoji"] == ":robot_face:"
    # should not be present in URL
    url = URLObject(resp.request.url)
    assert "token" not in url.query_dict


@requires_overridable_fixer
@responses.activate
def test_override_token_post():
    responses.add(responses.POST, "https://slack.com/api/chat.postMessage")

    app = Flask(__name__)
    slack_bp = make_slack_blueprint(
        client_id="foo", client_secret="bar",
        backend=MemoryBackend({"access_token": "abcde"}),
    )
    app.register_blueprint(slack_bp, url_prefix="/login")

    with app.test_request_context("/"):
        app.preprocess_request()
        resp = slack.post("chat.postMessage", data={
            "token": "xyz",
            "channel": "#general",
            "text": "ping",
            "icon_emoji": ":robot_face:",
        })
    request_data = url_decode(resp.request.body)
    assert request_data["token"] == "xyz"
    assert request_data["channel"] == "#general"
    assert request_data["text"] == "ping"
    assert request_data["icon_emoji"] == ":robot_face:"
    # should not be present
    url = URLObject(resp.request.url)
    assert "token" not in url.query_dict
