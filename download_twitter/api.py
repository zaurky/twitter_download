#!/usr/bin/python

import sys
from functools import wraps

from twython import Twython
from twython.exceptions import TwythonRateLimitError, TwythonError

from requests_oauthlib import OAuth1Session
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


class API(object):
    """
    Twitter API class, init Twython and OAuth1Session
    Add helpers
    """

    def __init__(self, config):
        """ Init the twitter api and a requests with the good crehencials """
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
    def get_friends(self):
        """ Get all friends IDS """
        return self.twitter.get_friends_ids()['ids']

    @exception_handler
    def get_lists(self):
        """ Get all user lists """
        return [group['name'] for group in self.twitter.show_lists()]

    @exception_handler
    def get_list_users(self, list_id):
        """ Get all users id from a list """
        return [user['id'] for user in
                api.twitter.get_list_members(list_id=list_id)['users']]
