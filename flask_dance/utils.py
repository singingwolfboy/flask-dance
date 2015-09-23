from __future__ import unicode_literals
import functools
from collections import MutableMapping


class FakeCache(object):
    """
    An object that mimics just enough of Flask-Cache's API to be compatible
    with our needs, but does nothing.
    """
    def get(self, key):
        return None
    def set(self, key, value):
        return None
    def delete(self, key):
        return None


def first(iterable, default=None, key=None):
    """
    Return the first truthy value of an iterable.
    Shamelessly stolen from https://github.com/hynek/first
    """
    if key is None:
        for el in iterable:
            if el:
                return el
    else:
        for el in iterable:
            if key(el):
                return el
    return default


sentinel = object()

def getattrd(obj, name, default=sentinel):
    """
    Same as getattr(), but allows dot notation lookup
    Source: http://stackoverflow.com/a/14324459
    """
    try:
        return functools.reduce(getattr, name.split("."), obj)
    except AttributeError as e:
        if default is not sentinel:
            return default
        raise
