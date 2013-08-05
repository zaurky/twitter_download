#!/usr/bin/python

from functools import wraps


class Cache(object):
    """ Container for cached values """


def put_in_cache(method):
    """
    Handle cache for method we call often and which result shoul not change
    """

    @wraps(method)
    def _cached_value(*args, **kwargs):
        if not args and not kwargs:
            value = getattr(Cache, method.__name__, None)

            if not value:
                value = method(*args, **kwargs)
                setattr(Cache, method.__name__, value)

            return value
        return method(*args, **kwargs)
    return _cached_value
