#!/usr/bin/python

import os
from functools import wraps
import pickle


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


class LastId(object):
    """ Load the last id file and save it when done """

    def __init__(self, config):
        """ Open or create the last id file """
        self.friends_last_id_file = config.get('path', 'friends_last_id_file')

        if os.path.exists(self.friends_last_id_file):
            print "retrieve %s" % self.friends_last_id_file
            pkl_file = open(self.friends_last_id_file, 'rb')
            self.friends_last_id = pickle.load(pkl_file)
            pkl_file.close()
        else:
            self.friends_last_id = {}

    def __del__(self):
        """
        When we init, we read the friend last id list from a file, we modify
        it all the process long, we have to backup it at the end.
        """
        print "backup %s"% self.friends_last_id_file
        pkl_file = open(self.friends_last_id_file, 'wb')
        pickle.dump(self.friends_last_id, pkl_file)
        pkl_file.close()
