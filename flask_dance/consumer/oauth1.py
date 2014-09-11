from __future__ import unicode_literals, print_function

import sys
from flask import request, url_for, redirect
from urlobject import URLObject
from requests_oauthlib import OAuth1Session
from oauthlib.oauth1 import SIGNATURE_HMAC, SIGNATURE_TYPE_AUTH_HEADER
from oauthlib.common import to_unicode
from .base import BaseOAuthConsumerBlueprint


class OAuth1SessionWithBaseURL(OAuth1Session):
    def __init__(self, base_url=None, *args, **kwargs):
        super(OAuth1SessionWithBaseURL, self).__init__(*args, **kwargs)
        self.base_url = URLObject(base_url)

    def prepare_request(self, request):
        if self.base_url:
            request.url = self.base_url.relative(request.url)
        print("URL = {}".format(request.url), file=sys.stderr)
        return super(OAuth1SessionWithBaseURL, self).prepare_request(request)


class OAuth1ConsumerBlueprint(BaseOAuthConsumerBlueprint):
    def __init__(self, name, import_name,
            client_key=None,
            client_secret=None,
            signature_method=SIGNATURE_HMAC,
            signature_type=SIGNATURE_TYPE_AUTH_HEADER,
            rsa_key=None,
            client_class=None,
            force_include_body=False,

            static_folder=None, static_url_path=None, template_folder=None,
            url_prefix=None, subdomain=None, url_defaults=None, root_path=None,

            login_url=None,
            authorized_url=None,
            base_url=None,
            request_token_url=None,
            access_token_url=None,
            authorization_url=None,
            redirect_url=None,
            redirect_to=None,

            **kwargs):

        if not redirect_url and not redirect_to:
            raise AttributeError("One of redirect_url or redirect_to must be defined")

        BaseOAuthConsumerBlueprint.__init__(
            self, name, import_name,
            static_folder=static_folder,
            static_url_path=static_url_path,
            template_folder=template_folder,
            url_prefix=url_prefix, subdomain=subdomain,
            url_defaults=url_defaults, root_path=root_path,
            login_url=login_url,
            authorized_url=authorized_url,
        )

        self.session = OAuth1SessionWithBaseURL(
            client_key=client_key,
            client_secret=client_secret,
            signature_method=signature_method,
            signature_type=signature_type,
            rsa_key=rsa_key,
            client_class=client_class,
            force_include_body=force_include_body,
            base_url=base_url,
            **kwargs
        )

        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url
        self.redirect_url = redirect_url
        self.redirect_to = redirect_to

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

    def assign_token_to_session(self, identifier=None):
        token = self.get_token(identifier=identifier)
        if token and "oauth_token" in token and "oauth_token_secret" in token:
            # This really, really violates the Law of Demeter, but
            # I don't see a better way to set these parameters. :(
            self.session.auth.client.resource_owner_key = to_unicode(token["oauth_token"])
            self.session.auth.client.resource_owner_secret = to_unicode(token["oauth_token_secret"])
