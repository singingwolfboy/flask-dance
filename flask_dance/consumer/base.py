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

        self.set_token_storage_session()
        self.logged_in_funcs = []
        self.before_app_request(self.assign_token_to_session)

    def login(self):
        raise NotImplementedError()

    def authorized(self):
        raise NotImplementedError()

    def assign_token_to_session(self):
        raise NotImplementedError

    def logged_in(self, func):
        """
        A decorator used to indicate a function to be run immediately after
        the OAuth dance is completed. The function will be called with the OAuth
        token as an argument. You can use this decorator on multiple functions,
        and they will all be run after the OAuth dance is completed.
        """
        self.logged_in_funcs.append(func)

    token = proxy_property(
        "token", pass_self=False,
        doc=("A proxy property for getting, setting, and deleting the stored "
             "OAuth token."),
    )

    def token_getter(self, func):
        """
        A decorator used to indicate the function used to retrieve a stored
        token from a completed OAuth dance.
        """
        self.get_token = func

    def token_setter(self, func):
        """
        A decorator used to indicate the function used to store a token
        from a completed OAuth dance, so that it can be retrieved later.
        """
        self.set_token = func

    def token_deleter(self, func):
        """
        A decorator used to indicate the function used to delete a
        previously-stored OAuth token.
        """
        self.delete_token = func

    def set_token_storage_session(self):
        key = "{name}_oauth_token".format(name=self.name)

        @self.token_getter
        def get_token():
            return flask.session.get(key)

        @self.token_setter
        def set_token(token):
            flask.session[key] = token

        @self.token_deleter
        def delete_token():
            del flask.session[key]

    def set_token_storage_sqlalchemy(self, model, session, user=None):
        """
        Set token accessors to work with a SQLAlchemy database for token
        storage/retrieval.
        """
        from sqlalchemy.orm.exc import NoResultFound

        @self.token_getter
        def get_token():
            query = session.query(model).filter_by(provider=self.name)
            if hasattr(model, "user"):
                u = user() if callable(user) else user
                query = query.filter_by(user=u)
            try:
                return query.one().token
            except NoResultFound:
                return None

        @self.token_setter
        def set_token(token):
            kwargs = {
                "provider": self.name,
                "token": token,
            }
            if hasattr(model, "user"):
                u = user() if callable(user) else user
                kwargs["user"] = u
            session.add(model(**kwargs))
            session.commit()

        @self.token_deleter
        def delete_token():
            query = session.query(model).filter_by(provider=self.name)
            if hasattr(model, "user"):
                u = user() if callable(user) else user
                query = query.filter_by(user=u)
            query.delete()
