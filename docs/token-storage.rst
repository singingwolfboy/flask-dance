Token Storage
=============
By default, OAuth access tokens are stored in the
:ref:`Flask session <flask:sessions>`. This means that if the user ever
clears their browser cookies, they will have to go through the OAuth flow again,
which is not good. You're better off storing access tokens
in a database or some other persistent store. To do that, just write custom
get and set functions, and attach them to the Blueprint object using the
:obj:`~flask_dance.consumer.OAuth2ConsumerBlueprint.token_getter` and
:obj:`~flask_dance.consumer.OAuth2ConsumerBlueprint.token_setter` decorators::

    @github_blueprint.token_setter
    def set_github_token(token):
        user = flask.g.user
        user.github_token = token
        db.session.add(user)
        db.commit()

    @github_blueprint.token_getter
    def get_github_token():
        user = flask.g.user
        return user.github_token

    @github_blueprint.token_deleter
    def delete_github_token():
        user = flask.g.user
        user.github_token = None
        db.session.add(user)
        db.commit()