#!/usr/bin/python
"""
Twitter module
"""

import operator
import pexif
from pexif import JpegFile

from .api import API
from .cache import LastId, FriendList, ListContent, AllTweets

import os
from distutils.dir_util import mkpath
from datetime import datetime


def sanitize(string):
    """
    Remove all non ascii chars to be able to put the string in exif
    """
    return unicode(string).encode('ascii', 'replace')


def is_retweet(status):
    """ says if a status is a retweet or not """
    return ('retweeted_status' in status
            and status['retweeted_status']['user']['screen_name']
                != status['user']['screen_name'])


def simplify_tweet(tweet):
    """ only get the information we use from a status """
    status = {
        'created_at': tweet['created_at'],
        'id': tweet['id'],
        'text': tweet['text'],
        'user': {
            'screen_name': tweet['user']['screen_name'],
            'name': tweet['user']['name'],
        },
    }
    if 'media' in tweet['entities']:
        status['entities'] = {
            'media': tweet['entities']['media'],
        }
    status['retweet'] = is_retweet(tweet)
    return status


class Twitter(API):
    """ add a layer over the twitter api to implement advanced behaviours """
    def __init__(self, config):
        """
        Init the path we will need to download (and the API)
        """
        API.__init__(self, config)

        self._image_path = "%s/" % config.get('path', 'image_path').rstrip('/')
        self._daily_path = "%s/" % config.get('path', 'daily_path').rstrip('/')

        self._daily = '%s%s/' % (self._daily_path,
            datetime.now().strftime('%Y%m%d'))

        self._retweet = 'retweet'

        self.friends_last_id = LastId(config)
        self.friends = FriendList(config)
        self.listcontent = ListContent(config)
        self.tweets = AllTweets(config)

    @staticmethod
    def should_get_image(_url, filepath):
        """
        Should we get this image demending on several considerations
        (does the file exists only right now)
        """
        return not os.path.exists(filepath)

    @staticmethod
    def put_exif(data, status):
        """
        Put the interesting exif data in a pexif image
          * ImageDescription
          * Artist
          * DateTimeOriginal
        """
        img = pexif.JpegFile.fromString(data)

        img.exif.primary.ImageDescription = sanitize(status['text'])

        if not img.exif.primary.has_key('Artist'):
            img.exif.primary.Artist = sanitize(status[u'user'][u'name'])

        if not img.exif.primary.has_key('DateTimeOriginal'):
            img.exif.primary.DateTimeOriginal = sanitize(status[u'created_at'])

        return img

    def prepare_dir(self, filepath):
        """
        Prepare what we are going to need on the file system for the next step
        """
        mkpath(os.path.dirname(filepath))

        if not os.path.exists(self._daily):
            mkpath(self._daily)

        for group_name in self.listcontent['list_content']:
            path = os.path.join(self._daily, group_name)
            if not os.path.exists(path):
                mkpath(path)

    def link_daily(self, filepath):
        """
        Create a link between the newly download file and daily dir
        """
        directory = os.path.dirname(filepath)
        first_level = os.path.basename(directory)

        shift_dir = os.path.dirname(directory)
        second_level = os.path.basename(shift_dir)
        third_level = os.path.basename(os.path.dirname(shift_dir))
        retweet = first_level == self._retweet

        if retweet:
            first_level = second_level
            second_level = third_level

        list_name = second_level
        if second_level == os.path.basename(self._image_path.rstrip('/')):
            list_name = ''

        try:
            link = os.path.join(self._daily,
                                list_name,
                                '%s_%s' % (
                                    os.path.basename(directory),
                                    os.path.basename(filepath),
                                ))
            os.symlink(filepath, link)
        except OSError:
            pass

    def write_data(self, media_id, data, status, filepath):
        """ write image data and exif when possible """
        try:
            img = self.put_exif(data, status)
            img.writeFile(filepath)
        except JpegFile.InvalidFile:
            print "      could not put exif in %s" % media_id
            with open(filepath, 'wb') as fdesc:
                fdesc.write(data)

    def get_list_content(self):
        """ Get list content and friends in list """
        return (self.listcontent['list_content'],
                self.listcontent['friend_in_list'])

    def retrieve_image(self, path, media_id, media_url, status):
        """ Retrieve the image """
        retweet = self._retweet if is_retweet(status) else ''
        filepath = os.path.join(path, retweet, media_id + '.jpg')
        if not self.should_get_image(media_url, filepath):
            print "      %s %s exists" % (
                    'retweet' if retweet else 'image',
                    media_id)
            return False

        data = self.get_image(media_url)
        if not data:
            print "      %s %s is empty" % (
                    'retweet' if retweet else 'image',
                    media_id)
            return False

        if retweet:
            print "      image %s is a retweet" % media_id

        self.prepare_dir(filepath)

        self.write_data(media_id, data, status, filepath)
        self.link_daily(filepath)
        return True

    def retrieve_all(self, statuses, path):
        """ loop over all the statuses and call `retrieve_image` on each """
        pic_nb = 0
        for status in statuses:
            for media_id, media_url in self.get_images_from_status(status):
                if self.retrieve_image(path, media_id, media_url, status):
                    pic_nb += 1

        if pic_nb:
            print "    * %s pics" % (pic_nb,)

        return pic_nb

    def run(self,):
        """
        Run the twitter image downloader process
        """
        list_content, friend_in_list = self.get_list_content()
        print "got %d lists %s" % (
                len(list_content),
                ', '.join([name for name in list_content]))
        print "%d friends in list" % (len(self.friends),)

        total_pic = 0
        not_affected_friends = []

        for friend_id in self.friends:
            since_id = self.friends_last_id.get(friend_id)
            is_in_list = friend_in_list.get(friend_id, '')

            statuses = self.get_statuses_for_friend(friend_id, since_id)
            if not statuses:
                continue

            username = statuses[0]['user']['screen_name'].replace('/', ' ')

            print "%s : %s %s" % (friend_id,
                                  username,
                                  "[%s]" % is_in_list if is_in_list else '')
            if not is_in_list:
                not_affected_friends.append(username)

            if since_id is None:
                print "    * User seems new to me"

            print "    * %d status retrieved" % (len(statuses),)

            path = os.path.join(self._image_path, is_in_list, username)
            total_pic += self.retrieve_all(statuses, path)

            print "    * last status id is %s" % (statuses[0]['id'],)
            self.friends_last_id[friend_id] = statuses[0]['id']

        if total_pic:
            print "Got %d images" % total_pic

        if not_affected_friends:
            print "Thoses friends are not in a group %s" % (
                    ', '.join(not_affected_friends))

    def refresh_friend(self):
        """ refresh the friend list cache """
        for key, value in self.get_friends():
            self.friends[key] = value

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

        statuses.extend([simplify_tweet(tweet) for tweet in tweets])

        self.tweets[friend_id] = statuses
        return True

    def cache_all_friends_tweets(self):
        """ loop over all friend and call `cache_all_friend_tweets` """
        count_treated = 0
        for friend_id in [str(key) for key in self.friends]:
            if self.cache_all_friend_tweets(friend_id):
                self.tweets.free(friend_id)
            count_treated += 1

        return count_treated

    def __repr__(self):
        return '<Twitter>'
