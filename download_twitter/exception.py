#!/usr/bin/python

import sys
from functools import wraps

from twython.exceptions import (TwythonRateLimitError,
                                TwythonError,
                                TwythonStreamError,
                                TwythonAuthError)
from requests.exceptions import ConnectionError


def display_method(method, args, kwargs):
    ret = "%s(%s, %s)" % (
            method.func_name,
            ', '.join([unicode(i) for i in args[1:]]),
            ', '.join(["%s=%s" % (k, v) for k, v in kwargs.items()]),
    )
    return ret


def exception_handler(method):
    """ Handle exceptions that could happen here """

    @wraps(method)
    def _handle_exceptions(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except ConnectionError, err:
            print "    connection error, %s" % display_method(method, args, kwargs)
        except TwythonRateLimitError, err:
            print err
            sys.exit(-1)
        except TwythonAuthError, err:
            print "    auth error, %s" % display_method(method, args, kwargs)
        except TwythonStreamError, err:
            print "    stream error, %s" % display_method(method, args, kwargs)
        except TwythonError, err:
            print "    error, %s" % display_method(method, args, kwargs)

    return _handle_exceptions
