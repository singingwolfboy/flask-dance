from flask_dance.contrib.twitter import make_twitter_blueprint, twitter
from flask_dance.consumer import OAuth1ConsumerBlueprint


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
