# coding=utf-8
from __future__ import unicode_literals

from pkg_resources import get_distribution
from .consumer import OAuth1ConsumerBlueprint, OAuth2ConsumerBlueprint

__version__ = get_distribution("flask_dance").version
