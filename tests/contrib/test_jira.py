from flask_dance.contrib.jira import make_jira_blueprint, jira
from flask_dance.consumer import OAuth1ConsumerBlueprint


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
    assert jira_bp.session.headers["Content-Type"] == "application/json"
