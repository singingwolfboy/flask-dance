import functools
from datetime import datetime


try:
    from datetime import timezone

    utc = timezone.utc
except ImportError:
    from datetime import timedelta, tzinfo

    class UTC(tzinfo):
        def utcoffset(self, dt):
            return timedelta(0)

        def tzname(self, dt):
            return "UTC"

        def dst(self, dst):
            return timedelta(0)

    utc = UTC()

try:
    from werkzeug.utils import invalidate_cached_property
except ImportError:
    from werkzeug._internal import _missing

    def invalidate_cached_property(obj, name):
        obj.__dict__[name] = _missing


class FakeCache:
    """
    An object that mimics just enough of Flask-Caching's API to be compatible
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


def timestamp_from_datetime(dt):
    """
    Given a datetime, in UTC, return a float that represents the timestamp for
    that datetime.

    http://stackoverflow.com/questions/8777753/converting-datetime-date-to-utc-timestamp-in-python#8778548
    """
    dt = dt.replace(tzinfo=utc)
    if hasattr(dt, "timestamp") and callable(dt.timestamp):
        return dt.replace(tzinfo=utc).timestamp()
    return (dt - datetime(1970, 1, 1, tzinfo=utc)).total_seconds()
