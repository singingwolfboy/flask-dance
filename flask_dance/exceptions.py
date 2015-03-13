# coding=utf-8
from __future__ import unicode_literals

class FlaskDanceException(Exception):
    "Base exception class that all others in this package inherit from"
    pass


class ProviderError(FlaskDanceException):
    def __init__(self, message, code=None, uri=None):
        self.message = message
        self.code = code
        self.uri = uri
        FlaskDanceException.__init__(self, message)
