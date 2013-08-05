#!/usr/bin/python

import sys
from functools import wraps

from twython.exceptions import TwythonRateLimitError, TwythonError
from requests.exceptions import ConnectionError


def exception_handler(method):
    """ Handle exceptions that could happen here """

    @wraps(method)
    def _handle_exceptions(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except ConnectionError, err:
            print "    connection error, %s (%s, %s)" % (method, args, kwargs)
        except TwythonRateLimitError, err:
            print err
            sys.exit(-1)
        except TwythonError, err:
            print "    error, %s (%s, %s)" % (method, args, kwargs)

    return _handle_exceptions
