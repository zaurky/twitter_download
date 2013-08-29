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
    """ Remove all non ascii chars to be able to put the string in exif """
    return unicode(string).encode('ascii', 'replace')


## status treatments
def is_retweet(status):
    """ says if a status is a retweet or not """
    return ('retweeted_status' in status
            and status['retweeted_status']['user']['screen_name']
                != status['user']['screen_name'])


def simplify_status(status):
    """ only get the information we use from a status """
    ret = {
        'created_at': status['created_at'],
        'id': status['id'],
        'text': status['text'],
        'user': {
            'screen_name': status['user']['screen_name'],
            'name': status['user']['name'],
        },
    }
    if 'media' in status['entities']:
        ret['entities'] = {
            'media': status['entities']['media'],
        }
    ret['restatus'] = is_retweet(status)
    return ret


def get_images_from_status(status):
    """ Extract medias from a twitter status """
    return [(media['id_str'], media['media_url'])
            for media in status['entities'].get('media', [])]


class Image(object):
    """ Tweeter image """
    img = None

    def __init__(self, media_id, filepath, data, status):
        """ initialise the tweeter image """
        self.media_id = media_id
        self.filepath = filepath
        self.data = data
        self.status = status

    @property
    def text(self):
        """ get status text from """
        return sanitize(self.status['text'])

    @property
    def name(self):
        """ get friend name """
        return sanitize(self.status['user']['name'])

    @property
    def created_at(self):
        """ get creation date """
        return sanitize(self.status['created_at'])

    def _put_exif(self):
        """
        Put the interesting exif data in a pexif image
          * ImageDescription
          * Artist
          * DateTimeOriginal
        """
        self.img = pexif.JpegFile.fromString(self.data)

        self.img.exif.primary.ImageDescription = self.text

        if not self.img.exif.primary.has_key('Artist'):
            self.img.exif.primary.Artist = self.name

        if not self.img.exif.primary.has_key('DateTimeOriginal'):
            self.img.exif.primary.DateTimeOriginal = self.created_at

    def write(self):
        """ write image data and exif when possible """
        try:
            self._put_exif()
            self.img.writeFile(self.filepath)
        except JpegFile.InvalidFile:
            print "      could not put exif in %s" % self.media_id
            with open(self.filepath, 'wb') as fdesc:
                fdesc.write(self.data)


class ImageFactory(object):
    """ ImageFactory to convert all statuses in `Image` """

    def __init__(self, api, config, listname, username):
        self._api = api
        self._image_path = "%s/" % config.get('path', 'image_path').rstrip('/')

        self._daily_path = "%s/" % config.get('path', 'daily_path').rstrip('/')

        self.path = os.path.join(self._image_path, listname, username)
        self._daily = '%s%s/' % (self._daily_path,
            datetime.now().strftime('%Y%m%d'))

        self._retweet = 'retweet'

    @staticmethod
    def should_get_image(_url, filepath):
        """
        Should we get this image demending on several considerations
        (does the file exists only right now)
        """
        return not os.path.exists(filepath)

    def prepare_dir(self, filepath):
        """
        Prepare what we are going to need on the file system for the next step
        """
        mkpath(os.path.dirname(filepath))

        if not os.path.exists(self._daily):
            mkpath(self._daily)

        for group_name in self._api.listcontent['list_content']:
            path = os.path.join(self._daily, group_name)
            if not os.path.exists(path):
                mkpath(path)

    def link_daily(self, filepath):
        """ Create a link between the newly download file and daily dir """
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

    def retrieve_image(self, media_id, media_url, status):
        """ Retrieve the image """
        retweet = self._retweet if is_retweet(status) else ''
        filepath = os.path.join(self.path, retweet, media_id + '.jpg')
        if not self.should_get_image(media_url, filepath):
            print "      %s %s exists" % (
                    'retweet' if retweet else 'image',
                    media_id)
            return False

        data = self._api.get_image(media_url)
        if not data:
            print "      %s %s is empty" % (
                    'retweet' if retweet else 'image',
                    media_id)
            return False

        if retweet:
            print "      image %s is a retweet" % media_id

        self.prepare_dir(filepath)
        Image(media_id, filepath, data, status).write()
        self.link_daily(filepath)
        return True

    def retrieve_all(self, statuses):
        """ loop over all the statuses and call `retrieve_image` on each """
        pic_nb = 0
        for status in statuses:
            for media_id, media_url in get_images_from_status(status):
                if self.retrieve_image(media_id, media_url, status):
                    pic_nb += 1

        if pic_nb:
            print "    * %s pics" % (pic_nb,)

        return pic_nb


class Twitter(API):
    """ add a layer over the twitter api to implement advanced behaviours """
    def __init__(self, config):
        """ Init the path we will need to download (and the API) """
        API.__init__(self, config)

        self.friends_last_id = LastId(config)
        self.friends = FriendList(config)
        self.listcontent = ListContent(config)
        self.tweets = AllTweets(config)

    def get_list_content(self):
        """ Get list content and friends in list """
        return (self.listcontent['list_content'],
                self.listcontent['friend_in_list'])

    def run(self,):
        """ Run the twitter image downloader process """
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

            img_factory = ImageFactory(self,
                                       self._config,
                                       is_in_list,
                                       username)
            total_pic += img_factory.retrieve_all(statuses)

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

        statuses.extend([simplify_status(tweet) for tweet in tweets])

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
