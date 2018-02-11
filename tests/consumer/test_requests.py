# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import pytest
import mock
from pkg_resources import parse_version
import requests_oauthlib
from flask_dance.consumer.requests import OAuth1Session, OAuth2Session


FAKE_OAUTH1_TOKEN = {
    "oauth_token": "abcdefg",
    "oauth_token_secret": "hijklmnop",
}
FAKE_OAUTH2_TOKEN = {
    "access_token": "deadbeef",
    "scope": ["custom"],
    "token_type": "bearer",
}


def test_oauth1session_authorized():
    bp = mock.Mock(token=FAKE_OAUTH1_TOKEN)
    sess = OAuth1Session(client_key="ckey", client_secret="csec", blueprint=bp)
    assert sess.authorized == True


def test_oauth1session_not_authorized():
    bp = mock.Mock(token=None)
    sess = OAuth1Session(client_key="ckey", client_secret="csec", blueprint=bp)
    assert sess.authorized == False


def test_oauth2session_authorized():
    bp = mock.Mock(token=FAKE_OAUTH2_TOKEN)
    sess = OAuth2Session(client_id="cid", blueprint=bp)
    assert sess.authorized == True


def test_oauth2session_not_authorized():
    bp = mock.Mock(token=None)
    sess = OAuth2Session(client_id="cid", blueprint=bp)
    assert sess.authorized == False


def test_oauth2session_token():
    bp = mock.Mock(token=FAKE_OAUTH2_TOKEN)
    sess = OAuth2Session(client_id="cid", blueprint=bp)
    assert sess.token == FAKE_OAUTH2_TOKEN


def test_oauth2session_unset_token():
    bp = mock.Mock(token=None)
    sess = OAuth2Session(client_id="cid", blueprint=bp)
    assert sess.token == None


def test_oauth2session_access_token():
    bp = mock.Mock(token=FAKE_OAUTH2_TOKEN)
    sess = OAuth2Session(client_id="cid", blueprint=bp)
    assert sess.access_token == "deadbeef"


def test_oauth2session_unset_access_token():
    bp = mock.Mock(token=None)
    sess = OAuth2Session(client_id="cid", blueprint=bp)
    assert sess.access_token == None
