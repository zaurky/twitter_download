#!/usr/bin/python

import os
from functools import wraps
import pickle
from types import DictType


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


class PklDict(DictType):
    """ Load a pkl file in an dict and give access to it """

    def __init__(self, filepath):
        self.filepath = filepath

        if os.path.exists(self.filepath):
            print "retrieve %s" % self.filepath
            pkl_file = open(self.filepath, 'rb')
            self._internal = pickle.load(pkl_file)
            pkl_file.close()
        else:
            self._internal = {}

    def __len__(self):
        return len(self._internal)

    def __getitem__(self, key):
        return self._internal.__getitem__(key)

    def __setitem__(self, key, value):
        return self._internal.__setitem__(key,  value)

    def __delitem__(self, key):
        return self._internal.__delitem__(key)

    def __iter__(self):
        return self._internal.__iter__()

    def get(self, key, value=None):
        return self._internal.get(key, value)

    def __repr__(self):
        return self._internal.__repr__()

    def __del__(self):
        """ backup internal into the pkl file at the end """
        print "backup %s"% self.filepath
        pkl_file = open(self.filepath, 'wb')
        pickle.dump(self._internal, pkl_file)
        pkl_file.close()


class LastId(PklDict):
    """ Load the last id file and save it when done """

    def __init__(self, config):
        """ Open or create the last id file """
        PklDict.__init__(self, config.get('path', 'friends_last_id_file'))


class FriendList(PklDict):
    """ Load the friend list file and save it when done """

    def __init__(self, config):
        """ Open or create the friend list file """
        PklDict.__init__(self, config.get('path', 'friends_list_file'))


class ListContent(PklDict):
    """ Load the list content file and save it when done """

    def __init__(self, config):
        """ Open or create the list content file """
        PklDict.__init__(self, config.get('path', 'list_content_file'))
