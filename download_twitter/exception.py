#!/usr/bin/python
"""
Everything that have to do with exceptions.
"""

from functools import wraps
from datetime import datetime

from twython.exceptions import (TwythonRateLimitError,
                                TwythonError,
                                TwythonStreamError,
                                TwythonAuthError)
from requests.exceptions import ConnectionError


def display_method(method, args, kwargs):
    """ return a string showing the twitter api call """
    ret = "%s(%s, %s)" % (
            method.func_name,
            ', '.join([unicode(i) for i in args[1:]]),
            ', '.join(["%s=%s" % (k, v) for k, v in kwargs.items()]),
    )
    return ret


class RateLimit(Exception):
    """ rate limit comes from twitter api """
    _from_twitter = True


class InternalRateLimit(RateLimit):
    """ rate limit comes from our rate limit system """
    _from_twitter = False


def exception_handler(method):
    """ Handle exceptions that could happen here """

    @wraps(method)
    def _handle_exceptions(*args, **kwargs):
        """ decorator """
        try:
            return method(*args, **kwargs)
        except ConnectionError, err:
            print "    connection error, %s" % display_method(method, args, kwargs)
        except TwythonRateLimitError, err:
            if err.error_code == 1337:
                raise InternalRateLimit()

            print err
            print "at %s" % datetime.now()
            raise RateLimit()
        except TwythonAuthError, err:
            print "    auth error, %s" % display_method(method, args, kwargs)
        except TwythonStreamError, err:
            print "    stream error, %s" % display_method(method, args, kwargs)
        except TwythonError, err:
            print "    error, %s" % display_method(method, args, kwargs)

    return _handle_exceptions
