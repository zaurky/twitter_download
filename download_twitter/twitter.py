#!/usr/bin/python
"""
Twitter module
"""

import operator

from .api import API
from .cache import LastId, FriendList, ListContent, AllTweets, WeightFriends
from .image import ImageFactory
from .utils import simplify_status
from .exception import RateLimit


class Twitter(API):
    """ add a layer over the twitter api to implement advanced behaviours """
    def __init__(self, config):
        """ Init the path we will need to download (and the API) """
        API.__init__(self, config)

        self.friends_last_id = LastId(config)
        self.friends = FriendList(config)
        self.weights = WeightFriends(config)
        self.listcontent = ListContent(config)
        self.tweets = AllTweets(config)

    def get_list_content(self):
        """ Get list content and friends in list """
        return (self.listcontent['list_content'],
                self.listcontent['friend_in_list'])

    @property
    def ponderated_weights(self):
        mux = {'Person': 1, 'Rss': 0.8, None: 0.85}

        return [(friend_id, weight *
                 mux[self.listcontent['friend_in_list'].get(friend_id)])
                 for friend_id, weight in self.weights.items()]

    def order_friends(self):
        """ Return the friends we queried the less often, """

        def less_call(el1, el2):
            """ compare on the 2nd element of the tuple """
            return cmp(el1[1], el2[1])

        return [(key, self.friends[key], weight)
                    for key, weight
                        in sorted(self.ponderated_weights, cmp=less_call)
                    if key in self.friends.keys()]

    def run(self,):
        """ Run the twitter image downloader process """
        list_content, friend_in_list = self.get_list_content()
        print "got %d lists %s" % (
                len(list_content),
                ', '.join([name for name in list_content]))
        print "%d friends in list" % (len(self.friends),)

        total_pic = 0
        not_affected_friends = []

        for friend_id, _, weight in self.order_friends():
            since_id = self.friends_last_id.get(friend_id)
            is_in_list = friend_in_list.get(friend_id, '')

            try:
                statuses = self.get_statuses_for_friend(friend_id, since_id)
            except RateLimit:
                print "Ratelimited"
                break

            if not statuses:
                self.weights[friend_id] = self.weights.get(friend_id, 0) + 1
                continue

            username = statuses[0]['user']['screen_name'].replace('/', ' ')

            msg = "%s : %s (%s) %s" % (friend_id,
                                  username,
                                  weight,
                                  "[%s]" % is_in_list if is_in_list else '')
            if not is_in_list:
                not_affected_friends.append(username)

            if since_id is None:
                msg += " (new user)"

            print msg

            msg = "    * %d status retrieved" % (len(statuses),)

            img_factory = ImageFactory(self,
                                       self._config,
                                       is_in_list,
                                       username)
            friend_pic, retweets = img_factory.retrieve_all(statuses)

            if friend_pic:
                msg += " : %s pics%s" % (friend_pic,
                                            (' with %s retweets' % retweets)
                                             if retweets else '')

            total_pic += friend_pic

            msg += " (until %s)" % (statuses[0]['id'],)
            self.friends_last_id[friend_id] = statuses[0]['id']

            if friend_pic < 2:
                self.weights[friend_id] = self.weights.get(friend_id, 0) + 1

            print msg

        if total_pic:
            print "Got %d images" % total_pic

        if not_affected_friends:
            print "Thoses friends are not in a group %s" % (
                    ', '.join(not_affected_friends))

    def refresh_friend(self):
        """ refresh the friend list cache """
        for key, value in self.get_friends():
            self.friends[key] = value
            self.weights[key] = self.weights.get(key, 0)

    def refresh_lists(self):
        """ refresh the list content cache """
        for key, value in self.retrieve_list_content().items():
            self.listcontent[key] = value

    def cache_all_friend_tweets(self, friend_id):
        """ get all/missing friends statuses and cache their simple info """
        last = None
        statuses = []
        if friend_id in self.tweets:
            statuses = self.tweets[friend_id]
            last = max(statuses, key=operator.itemgetter('id'))['id']

        tweets = self.get_statuses_for_friend(friend_id, last)
        if not tweets:
            return False

        print "%s friend has %d statuses %s" % (
                friend_id, len(tweets),
                'since %s' % last if last else '')

        statuses.extend([simplify_status(tweet) for tweet in tweets])

        self.tweets[friend_id] = statuses
        return True

    def cache_all_friends_tweets(self):
        """ loop over all friend and call `cache_all_friend_tweets` """
        count_treated = 0
        for friend_id in [str(key) for key in self.friends]:
            try:
                if self.cache_all_friend_tweets(friend_id):
                    self.tweets.free(friend_id)
                count_treated += 1
            except RateLimit:
                print "Ratelimited"
                break

        return count_treated

    def __repr__(self):
        return '<Twitter>'
