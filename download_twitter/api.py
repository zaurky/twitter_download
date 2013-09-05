#!/usr/bin/python

from functools import wraps
from twython import Twython
from requests_oauthlib import OAuth1Session

from .exception import exception_handler
from .cache import put_in_cache


def paginate(extract, ret_filter):
    def decorator(method):
        @wraps(method)
        def _paginate(*args, **kwargs):
            cursor = -1
            data = []

            while cursor:
                kwargs['cursor'] = cursor
                ldata = method(*args, **kwargs)
                cursor = ldata['next_cursor']
                data.extend(ldata[extract])

            return [[datum[key] for key in ret_filter] for datum in data]
        return _paginate
    return decorator


from datetime import datetime
from download_twitter.cache import PklDict
class Ratelimit(PklDict):
    def __init__(self, config):
        """ Open or create the ratelimit file """
        PklDict.__init__(self, config.get('path', 'ratelimit_file'))
        self.ratelimit = dict(config.items('ratelimit'))

    def call(self, method, *attr, **kwargs):
        pass

class API(object):
    """
    Twitter API class, init Twython and OAuth1Session
    Add helpers
    """

    def __init__(self, config):
        """ Init the twitter api and a requests with the good crehencials """
        self._config = config

        consumer_key = config.get('main', 'consumer_key')
        consumer_secret = config.get('main', 'consumer_secret')
        access_key = config.get('main', 'access_key')
        access_secret = config.get('main', 'access_secret')

        self.twitter = Twython(
                            consumer_key,
                            consumer_secret,
                            access_key,
                            access_secret)
        self.request = OAuth1Session(
                            consumer_key,
                            consumer_secret,
                            access_key,
                            access_secret)

        if config.getboolean('debug', 'twitter_calls'):
            self.twitter._true_request = self.twitter._request

            def debug_request(url, *args, **kwargs):
                print "%s %s" % (url, kwargs)
                return self.twitter._true_request(url, *args, **kwargs)

            self.twitter._request = debug_request

    @exception_handler
    def get_image(self, url):
        """ Retrieve data from the url """
        request = self.request.get(url)
        return request.content

    def get_statuses(self, friend_id, max_id=None, since_id=None):
        """ Get all the status a friend published """
        statuses = self.twitter.get_user_timeline(
                        user_id=friend_id,
                        count=200,
                        include_rts=1,
                        max_id=max_id,
                        since_id=since_id)

        if len(statuses) == 200:
            last = statuses[-1]['id']
            statuses.extend(self.get_statuses(friend_id, max_id=last))

        return statuses

    @exception_handler
    def get_statuses_for_friend(self, friend_id, since_id):
        """ Get all statuses since `since_id` for this friend """
        return self.get_statuses(friend_id, since_id=since_id)

    @exception_handler
    def get_friend(self, user_id=None, user_name=None):
        """ Get a friend based on it's id or name """
        assert user_id or user_name, 'You must give a name or id'
        user = self.twitter.show_user(friend_id=user_id,
                                      screen_name=user_name)
        return user['id'], user['screen_name']

    @put_in_cache
    @exception_handler
    @paginate('users', ['id', 'screen_name'])
    def get_friends(self, cursor=-1):
        """ Cached call - Get all friends (id, name) """
        return self.twitter.get_friends_list(cursor=cursor)

    @exception_handler
    def get_list(self, list_id=None, list_name=None):
        """ Get a list based on it's id or name """
        assert list_id or list_name, 'You must give a name or id'
        lists = self.get_lists()
        if list_name:
            return [group for group in lists if group[1] == list_name][0]
        else:
            return [group for group in lists if group[0] == list_id][0]

    @put_in_cache
    @exception_handler
    def get_lists(self):
        """ Cached call - Get all our lists (id, name) """
        return [(group['id'], group['name'])  for group in self.twitter.show_lists()]

    @exception_handler
    @paginate('users', ['id', 'screen_name'])
    def get_list_users(self, list_id, cursor=-1):
        """ Get all users id from a list """
        return self.twitter.get_list_members(list_id=list_id, cursor=cursor)

    @exception_handler
    def put_user_in_list(self, list_name, user_name):
        """
        WARN : Need RW permissions
        Put a user in the given list.
        """
        list_id, _list_name = self.get_list(list_name=list_name)
        user_id, _user_name = self.get_friend(user_name=user_name)

        print "putting %s (%s) in list %s (%s)" % (
               user_name, user_id, list_name, list_id)
        self.twitter.create_list_members(list_id=list_id, user_id=user_id)
        return True

    @exception_handler
    def del_user_from_list(self, list_name, user_name):
        """
        WARN : Need RW permissions
        Remove a user from the given list.
        """
        list_id, _list_name = self.get_list(list_name=list_name)
        user_id, _user_name = self.get_friend(user_name=user_name)

        print "removing %s (%s) from list %s (%s)" % (
               user_name, user_id, list_name, list_id)
        self.twitter.delete_list_member(list_id=list_id, user_id=user_id)
        return True

    def retrieve_list_content(self):
        """
        Get list content and friends in list
        """
        list_content = {}
        friend_in_list = {}

        for list_id, list_name in self.get_lists():
            friends = dict(self.get_list_users(list_id))
            list_content[list_name] = friends.keys()
            friend_in_list.update(
                    dict([(friend_id, list_name) for friend_id in friends]))
        return {
            'list_content': list_content,
            'friend_in_list': friend_in_list,
        }

    def __repr__(self):
        return '<API>'
