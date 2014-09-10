from __future__ import unicode_literals, print_function

import types
from distutils.version import StrictVersion
import flask
from flask_dance.utils import proxy_property


class BaseOAuthConsumerBlueprint(flask.Blueprint):
    def __init__(self, name, import_name,
            static_folder=None, static_url_path=None, template_folder=None,
            url_prefix=None, subdomain=None, url_defaults=None, root_path=None,
            login_url=None, authorized_url=None):

        bp_kwargs = dict(
            name=name,
            import_name=import_name,
            static_folder=static_folder,
            static_url_path=static_url_path,
            template_folder=template_folder,
            url_prefix=url_prefix,
            subdomain=subdomain,
            url_defaults=url_defaults,
            root_path=root_path,
        )
        # `root_path` didn't exist until 1.0
        if StrictVersion(flask.__version__) < StrictVersion('1.0'):
            del bp_kwargs["root_path"]
        flask.Blueprint.__init__(self, **bp_kwargs)

        login_url = login_url or "/{bp.name}"
        authorized_url = authorized_url or "/{bp.name}/authorized"

        self.add_url_rule(
            rule=login_url.format(bp=self),
            endpoint="login",
            view_func=self.login,
        )
        self.add_url_rule(
            rule=authorized_url.format(bp=self),
            endpoint="authorized",
            view_func=self.authorized,
        )

        self.create_token_accessors()
        self.before_app_request(self.assign_token_to_session)

    def login(self):
        raise NotImplementedError()

    def authorized(self):
        raise NotImplementedError()

    def assign_token_to_session(self):
        raise NotImplementedError

    def logged_in_callback(self, token):
        pass

    def logged_in(self, func):
        self.logged_in_callback = types.MethodType(func, self)

    token = proxy_property("token", pass_self=False)

    def token_getter(self, func):
        self.get_token = func

    def token_setter(self, func):
        self.set_token = func

    def token_deleter(self, func):
        self.delete_token = func

    def create_token_accessors(self):
        key = "{name}_oauth_token".format(name=self.name)

        @self.token_getter
        def get_token(identifier=None):
            return flask.session.get(key)

        @self.token_setter
        def set_token(value, identifier=None):
            flask.session[key] = value

        @self.token_deleter
        def delete_token(identifier=None):
            del flask.session[key]
