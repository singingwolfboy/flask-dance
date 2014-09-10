from flask_dance.consumer import OAuth2ConsumerBlueprint


def make_github_blueprint(client_id, client_secret, scope=None,
                          redirect_url=None, redirect_to=None,
                          login_url=None, authorized_url=None):
    github_bp = OAuth2ConsumerBlueprint("github", __name__,
        client_id=client_id,
        client_secret=client_secret,
        base_url="https://api.github.com/",
        authorization_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
    )
    return github_bp
