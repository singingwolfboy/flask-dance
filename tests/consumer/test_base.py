from __future__ import unicode_literals

import pytest
import mock
from flask_dance.consumer.base import BaseOAuthConsumerBlueprint


def test_not_impl():
    bp = BaseOAuthConsumerBlueprint("test", __name__)
    with pytest.raises(NotImplementedError):
        bp.login()
    with pytest.raises(NotImplementedError):
        bp.authorized()
    with pytest.raises(NotImplementedError):
        bp.load_token()


def test_default_token_getter():
    bp = BaseOAuthConsumerBlueprint("test", __name__)
    with mock.patch("flask_dance.consumer.base.flask") as mock_flask:
        bp.token
    mock_flask.session.get.assert_called_with("test_oauth_token")


def test_default_token_setter():
    bp = BaseOAuthConsumerBlueprint("test", __name__)
    with mock.patch("flask_dance.consumer.base.flask") as mock_flask:
        bp.token = "test"
    mock_flask.session.__setitem__.assert_called_with("test_oauth_token", "test")


def test_default_token_deleter():
    bp = BaseOAuthConsumerBlueprint("test", __name__)
    with mock.patch("flask_dance.consumer.base.flask") as mock_flask:
        del bp.token
    mock_flask.session.__delitem__.assert_called_with("test_oauth_token")


def test_custom_token_getter():
    bp = BaseOAuthConsumerBlueprint("test", __name__)
    mock_getter = mock.Mock()
    bp.token_getter(mock_getter)

    bp.token
    mock_getter.assert_called_with()


def test_custom_token_setter():
    bp = BaseOAuthConsumerBlueprint("test", __name__)
    mock_setter = mock.Mock()
    bp.token_setter(mock_setter)

    bp.token = "test"
    mock_setter.assert_called_with("test")


def test_custom_token_deleter():
    bp = BaseOAuthConsumerBlueprint("test", __name__)
    mock_deleter = mock.Mock()
    bp.token_deleter(mock_deleter)

    del bp.token
    mock_deleter.assert_called_with()
