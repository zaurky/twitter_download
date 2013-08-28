#!/usr/bin/python

import os
from os.path import isfile

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


class MultiPkl(DictType):
    def __init__(self, filepath):
        self.filepath = filepath
        self._loaded = {}
        self._modified = set()

    def _filenames(self, key):
        return os.path.join(self.filepath, "%s" % key)

    def __list_files(self):
        mypath = self.filepath
        return [f for f in os.listdir(mypath) if isfile(os.path.join(mypath, f))]

    def __len__(self):
        return len(self.__list_files())

    def __getitem__(self, key):
        keyfile = self._filenames(key)
        if not os.path.exists(keyfile):
            raise KeyError('%s does not exists' % key)

        if key not in self._loaded:
            print "retrieve %s" % keyfile
            pkl_file = open(keyfile, 'rb')
            self._loaded[key] = pickle.load(pkl_file)
            pkl_file.close()

        return self._loaded[key]

    def __setitem__(self, key, value):
        self._loaded[key] = value
        self._modified.add(key)

    def __delitem__(self, key):
        raise NotImplemented('cant del on MultiPkl right now')

    def __iter__(self):
        return self.__list_files()

    def get(self, key, value=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            pass

        return value

    def free(self, key):
        if key in self._modified:
            keyfile = self._filenames(key)
            print "backup %s"% keyfile
            pkl_file = open(keyfile, 'wb')
            pickle.dump(self._loaded[key], pkl_file)
            pkl_file.close()
        else:
            self._loaded.pop(key)
        self._modified.discard(key)

    def __contains__(self, key):
        return key in self.__list_files()

    def __repr__(self):
        return '{%s}' % ', '.join(self.__list_files())

    def __del__(self):
        for key in self._modified:
            self.free(key)


class AllTweets(MultiPkl):
    def __init__(self, config):
        """ Open or create the all tweets dict """
        MultiPkl.__init__(self, config.get('path', 'tweets_dir'))
