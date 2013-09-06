#!/usr/bin/python

import sys
from functools import wraps
from datetime import datetime

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
            if err.error_code != 1337:
                print err
                print "at %s" % datetime.now()
                sys.exit(-1)
            sys.exit(0)
        except TwythonAuthError, err:
            print "    auth error, %s" % display_method(method, args, kwargs)
        except TwythonStreamError, err:
            print "    stream error, %s" % display_method(method, args, kwargs)
        except TwythonError, err:
            print "    error, %s" % display_method(method, args, kwargs)

    return _handle_exceptions
