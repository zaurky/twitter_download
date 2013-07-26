#!/usr/bin/python

import pexif

from twython import Twython
from twython.exceptions import TwythonRateLimitError

from requests.exceptions import ConnectionError
from requests_oauthlib import OAuth1Session

import os
import sys
import pickle
from distutils.dir_util import mkpath
from datetime import datetime


def sanitize(string):
    """
    Remove all non ascii chars to be able to put the string in exif
    """
    return unicode(string).encode('ascii', 'replace')


class Twitter(object):
    def __init__(self, config):
        """
        Init the twitter api and a requests with the good crehencials
        """
        consumer_key = config.get('main', 'consumer_key'),
        consumer_secret = config.get('main', 'consumer_secret'),
        access_key = config.get('main', 'access_key'),
        access_secret = config.get('main', 'access_secret'))

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

        self.data_dir = '/home/olivier/Project/twitter/'
        self.friends_last_id_file = '%sfriends_last_id.pkl' % self.data_dir
        self.image_path = '%simages/' % self.data_dir
        self.daily = '%s/daily/%s/' % (
                            self.image_path,
                            datetime.now().strftime('%Y%m%d'),
                        )

        if os.path.exists(self.friends_last_id_file):
            pkl_file = open(self.friends_last_id_file, 'rb')
            self.friends_last_id = pickle.load(pkl_file)
            pkl_file.close()
        else:
            self.friends_last_id = {}

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

    def should_get_image(self, url, filepath):
        """
        Should we get this image demending on several considerations
        (does the file exists only right now)
        """
        return not os.path.exists(filepath)

    def get_image(self, url):
        """
        Retrieve data from the url
        """
        try:
            r = self.request.get(url)
            return r.content
        except ConnectionError:
            print "    connection error, didn't get %s" % (url,)

    def put_exif(self, data, status):
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

    def write_image(self, img, filepath):
        """
        Take a pexif image, write it in filepath and add a link for dailies
        """
        directory = os.path.dirname(filepath)
        mkpath(directory)

        img.writeFile(filepath)

        if not os.path.exists(self.daily):
            mkpath(self.daily)

        try:
            os.symlink(
                filepath,
                os.path.join(self.daily, '%s_%s' % (
                        os.path.basename(directory),
                        os.path.basename(filepath),
                )))
        except OSError:
            pass

        return True

    @staticmethod
    def get_images_from_status(status):
        """
        Extract medias from a twitter status
        """
        return [(media['id_str'], media['media_url'])
                for media in status['entities'].get('media', [])]

    def run(self,):
        try:
            friend_ids = self.twitter.get_friends_ids()['ids']
        except ConnectionError:
            print "    connection error, didn't get friends_ids"
            return

        print "%d friends in list" % (len(friend_ids),)


        for friend_id in friend_ids:
            try:
                statuses = self.get_statuses(
                                friend_id,
                                since_id=self.friends_last_id.get(friend_id))
            except TwythonRateLimitError, err:
                print err
                sys.exit(-1)

            if not statuses:
                continue

            username = statuses[0]['user']['screen_name'].replace('/', ' ')

            print "%s : %s" % (friend_id, username)
            print "    * %d status retrieved" % (len(statuses),)

            pic_nb = 0
            path = self.image_path + username

            for status in statuses:
                for media_id, media_url in self.get_images_from_status(status):
                    filepath = path + '/' + media_id + '.jpg'

                    if not self.should_get_image(media_url, filepath):
                        continue

                    data = self.get_image(media_url)
                    if not data:
                        continue

                    img = self.put_exif(data, status)
                    self.write_image(img, filepath)
                    pic_nb += 1

            if pic_nb:
                print "    * %s pics" % (pic_nb,)

            print "    * last status id is %s" % (statuses[0]['id'],)
            self.friends_last_id[friend_id] = statuses[0]['id']

    def __del__(self):
        """
        When we init, we read the friend last id list from a file, we modify
        it all the process long, we have to backup it at the end.
        """
        print "backup %s"% self.friends_last_id_file
        pkl_file = open(self.friends_last_id_file, 'wb')
        pickle.dump(self.friends_last_id, pkl_file)
        pkl_file.close()
        #return object.__del__(self)
