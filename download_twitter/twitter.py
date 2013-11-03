#!/usr/bin/python
"""
Twitter module
"""

from datetime import datetime
import operator

from .api import API
from .cache import (LastId, FriendList, ListContent, AllTweets, WeightFriends,
                    DeletedFriends)
from .image import MediaFactory
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
        return (self.listcontent.get('list_content', []),
                self.listcontent.get('friend_in_list', {}))

    @property
    def ponderated_weights(self):
        """
        the weight depend on the number of call done factor
        the list friend is in
        """
        mux = {'Person': 1, 'Rss': 0.8, None: 0.85}

        return [(friend_id, weight *
                 mux[self.listcontent.get('friend_in_list', {}).get(friend_id)])
                 for friend_id, weight in self.weights.items()]

    def order_friends(self):
        """ Return the friends we queried the less often, """

        def less_call(el1, el2):
            """ compare on the 2nd element of the tuple """
            return cmp(el1[1], el2[1])

        weights = sorted(self.ponderated_weights, cmp=less_call)

        return [(key, self.friends[key], weight)
                    for key, weight in weights
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
            if not is_in_list:
                not_affected_friends.append(username)

            print ("%(friend_id)s : %(name)s (%(weight)s)%(in_list)s"
                   "%(is_new)s" % {
                        'friend_id': friend_id,
                        'name': username,
                        'weight': weight,
                        'in_list': " [%s]" % is_in_list if is_in_list else '',
                        'is_new': ' (new user)' if not since_id else '',
                  })

            media_factory = MediaFactory(self,
                                       self._config,
                                       is_in_list,
                                       username)

            images, images_rt, videos, videos_rt = media_factory.retrieve_all(statuses)
            total_pic += images
            self.friends_last_id[friend_id] = statuses[0]['id']

            if images < 2:
                self.weights[friend_id] = self.weights.get(friend_id, 0) + 1

            print ("    * %(statuses)d status retrieved %(images)s pics "
                   "with %(images_rt)s retweets and %(videos)s videos (until %(last_id)s)" % {
                        'statuses': len(statuses),
                        'images': images,
                        'images_rt': images_rt,
                        'videos': videos,
                        'videos_rt': videos_rt,
                        'last_id': statuses[0]['id'],
                  })

        if total_pic:
            print "Got %d images" % total_pic

        if not_affected_friends:
            print "Thoses friends are not in a group %s" % (
                    ', '.join(not_affected_friends))

    def refresh_friend(self):
        """ refresh the friend list cache """
        old_friends = self.friends.keys()

        for key, value in self.get_friends():
            self.friends[key] = value
            self.weights[key] = self.weights.get(key, 0)
            if key in old_friends:
                old_friends.remove(key)

        deleted_friends = DeletedFriends(self._config)
        for friend_id in old_friends:
            deleted_friends[friend_id] = datetime.now()

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
        def index(array, element):
            try:
                return array.index(element)
            except ValueError:
                return -1

        friend_ids = [(index(self.tweets.keys(), str(friend_id)), friend_id)
                      for friend_id in self.friends.keys()]
        friend_ids.sort()
        friend_ids = [i[1] for i in friend_ids]

        for friend_id in [str(key) for key in friend_ids]:
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
