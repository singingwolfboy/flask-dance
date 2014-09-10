from flask_dance.consumer import OAuth1ConsumerBlueprint


def make_twitter_blueprint(api_key, api_secret,
                           redirect_url=None, redirect_to=None):
    twitter_bp = OAuth1ConsumerBlueprint("twitter", __name__,
        client_key=api_key,
        client_secret=api_secret,
        request_token_url="https://api.twitter.com/oauth/request_token",
        access_token_url="https://api.twitter.com/oauth/access_token",
        authorization_url="https://api.twitter.com/oauth/authorize",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
    )
    return twitter_bp