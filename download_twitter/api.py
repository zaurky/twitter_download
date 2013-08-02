#!/usr/bin/python

import sys

from twython import Twython
from twython.exceptions import TwythonRateLimitError, TwythonError

from requests_oauthlib import OAuth1Session
from requests.exceptions import ConnectionError


class API(object):
    """
    Twitter API class, init Twython and OAuth1Session
    Add helpers
    """

    def __init__(self, config):
        """
        Init the twitter api and a requests with the good crehencials
        """
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

    def get_image(self, url):
        """
        Retrieve data from the url
        """
        try:
            request = self.request.get(url)
            return request.content
        except ConnectionError:
            print "    connection error, didn't get %s" % (url,)

    def get_statuses(self, friend_id, max_id=None, since_id=None):
        """
        Get all the status a friend published
        """
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

    def get_statuses_for_friend(self, friend_id, since_id):
        """
        Get all statuses since `since_id` for this friend
        """
        try:
            return self.get_statuses(
                            friend_id,
                            since_id=since_id)
        except ConnectionError, err:
            print "    connection error, didn't get statuses for %s" % friend_id
        except TwythonRateLimitError, err:
            print err
            sys.exit(-1)
        except TwythonError, err:
            print "Couln't find statuses for %s" % friend_id

    def get_friends(self):
        """ Get all friends IDS """
        try:
            return self.twitter.get_friends_ids()['ids']
        except ConnectionError:
            print "    connection error, didn't get friends_ids"
