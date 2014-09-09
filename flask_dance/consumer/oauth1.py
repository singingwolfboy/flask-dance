from __future__ import unicode_literals, print_function

import types

from flask import Blueprint, request, session, url_for, redirect, flash
from requests_oauthlib import OAuth1Session, OAuth2Session
from oauthlib.oauth1 import SIGNATURE_HMAC, SIGNATURE_TYPE_AUTH_HEADER
from .utils import proxy_property


class OAuth1ConsumerBlueprint(Blueprint):
    def __init__(self, name, import_name,
            client_key=None,
            client_secret=None,
            signature_method=SIGNATURE_HMAC,
            signature_type=SIGNATURE_TYPE_AUTH_HEADER,
            rsa_key=None,
            client_class=None,
            force_include_body=False,

            static_folder=None, static_url_path=None, template_folder=None,
            url_prefix=None, subdomain=None, url_defaults=None,

            base_url=None,
            request_token_url=None,
            access_token_url=None,
            authorization_url=None,
            redirect_url=None,
            redirect_to=None,

            **kwargs):

        if not redirect_url and not redirect_to:
            raise AttributeError("One of redirect_url or redirect_to must be defined")

        Blueprint.__init__(
            self, name, import_name,
            static_folder=static_folder,
            static_url_path=static_url_path,
            template_folder=template_folder,
            url_prefix=url_prefix, subdomain=subdomain,
            url_defaults=url_defaults, # root_path=root_path,
        )

        self.session = OAuth1Session(
            client_key=client_key,
            client_secret=client_secret,
            signature_method=signature_method,
            signature_type=signature_type,
            rsa_key=rsa_key,
            client_class=client_class,
            force_include_body=force_include_body,
            **kwargs
        )

        self.base_url = base_url  # TODO: DefaultURLSession class? Composition?
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url
        self.redirect_url = redirect_url
        self.redirect_to = redirect_to

        self.add_url_rule(
            rule="/login/{name}".format(name=self.name),
            endpoint="login",
            view_func=self.login,
        )
        self.add_url_rule(
            rule="/login/{name}/authorized".format(name=self.name),
            endpoint="authorized",
            view_func=self.authorized,
        )

        self.create_token_accessors()

    def login(self):
        callback_uri = url_for(
            ".authorized", next=request.args.get('next'), _external=True,
        )
        response = self.session.fetch_request_token(self.request_token_url)
        url = self.session.authorization_url(
            self.authorization_url, oauth_callback=callback_uri,
        )
        return redirect(url)

    def authorized(self):
        next_url = request.args.get('next') or self.redirect_url or url_for(self.redirect_to)
        self.session.parse_authorization_response(request.url)
        token = self.session.fetch_access_token(self.access_token_url)
        self.logged_in_callback(token)
        self.token = token
        return redirect(next_url)

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
            return session.get(key)

        @self.token_setter
        def set_token(value, identifier=None):
            session[key] = value

        @self.token_deleter
        def delete_token(identifier=None):
            del session[key]
