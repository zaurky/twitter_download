#!/usr/bin/python

import pexif
from pexif import JpegFile

from .api import API

import os
import pickle
from distutils.dir_util import mkpath
from datetime import datetime


def sanitize(string):
    """
    Remove all non ascii chars to be able to put the string in exif
    """
    return unicode(string).encode('ascii', 'replace')


class Twitter(API):
    def __init__(self, config):
        """
        Init the path we will need to download (and the API)
        """
        API.__init__(self, config)

        self.data_dir = config.get('path', 'data_dir')

        self.friends_last_id_file = config.get('path', 'friends_last_id_file')
        self.image_path = "%s/" % config.get('path', 'image_path').rstrip('/')
        self.daily_path = "%s/" % config.get('path', 'daily_path').rstrip('/')

        self.daily = '%s%s/' % (self.daily_path,
            datetime.now().strftime('%Y%m%d'))

        if os.path.exists(self.friends_last_id_file):
            print "retrieve %s" % self.friends_last_id_file
            pkl_file = open(self.friends_last_id_file, 'rb')
            self.friends_last_id = pickle.load(pkl_file)
            pkl_file.close()
        else:
            self.friends_last_id = {}

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

        if not os.path.exists(self.daily):
            mkpath(self.daily)

        for _group_id, group_name in self.get_lists():
            path = os.path.exists(os.path.join(self.daily, group_name))
            print path
            if not path:
                mkpath(path)

    def link_daily(self, filepath):
        """
        Create a link between the newly download file and daily dir
        """
        directory = os.path.dirname(filepath)
        list_name = os.path.basename(os.path.dirname(directory))

        if list_name == os.path.basename(self.image_path):
            list_name = ''

        try:
            link = os.path.join(self.daily,
                                list_name,
                                '%s_%s' % (
                                    os.path.basename(directory),
                                    os.path.basename(filepath),
                                ))
            print link
            os.symlink(filepath, link)
        except OSError:
            pass

    @staticmethod
    def write_image(img, filepath):
        """
        Take a pexif image, write it in filepath and add a link for dailies
        """
        img.writeFile(filepath)

    @staticmethod
    def write_data(data, filepath):
        """
        Take data, write it in filepath and add a link for dailies
        """
        with open(filepath, 'wb') as fdesc:
            fdesc.write(data)

    @staticmethod
    def get_images_from_status(status):
        """
        Extract medias from a twitter status
        """
        return [(media['id_str'], media['media_url'])
                for media in status['entities'].get('media', [])]

    def get_list_content(self):
        """
        Get list content and friends in list
        """
        list_content = {}
        friend_in_list = {}

        for list_id, list_name in self.get_lists():
            friends = self.get_list_users(list_id)
            list_content[list_name] = friends
            friend_in_list.update(
                    dict([(friend_id, list_name) for friend_id in friends]))
        print "got %d lists" % len(list_content)
        print list_content
        return list_content, friend_in_list

    def retrieve_image(self, path, media_id, media_url, status):
        """
        Retrieve the image
        """
        filepath = path + '/' + media_id + '.jpg'

        if not self.should_get_image(media_url, filepath):
            return False

        data = self.get_image(media_url)
        if not data:
            return False

        self.prepare_dir(filepath)

        try:
            img = self.put_exif(data, status)
            self.write_image(img, filepath)
        except JpegFile.InvalidFile:
            print "could not put exif in %s" % media_id
            self.write_data(data, filepath)

        self.link_daily(filepath)
        return True

    def retrieve_all(self, statuses, path):
        pic_nb = 0
        for status in statuses:
            for media_id, media_url in self.get_images_from_status(status):
                if self.retrieve_image(path, media_id, media_url, status):
                    pic_nb += 1

        if pic_nb:
            print "    * %s pics" % (pic_nb,)

    def run(self,):
        """
        Run the twitter image downloader process
        """
        list_content, friend_in_list = self.get_list_content()

        friends = self.get_friends()
        print "%d friends in list" % (len(friends),)

        for friend_id, _friend_name in friends:
            since_id = self.friends_last_id.get(friend_id)
            is_in_list = friend_in_list.get(friend_id, '')

            statuses = self.get_statuses_for_friend(friend_id, since_id)
            if not statuses:
                print "No new statuses for %s" % friend_id
                continue

            username = statuses[0]['user']['screen_name'].replace('/', ' ')

            print "%s : %s %s" % (friend_id,
                                  username,
                                  "[%s]" % is_in_list if is_in_list else '')
            if since_id is None:
                print "    * User seems new to me"

            print "    * %d status retrieved" % (len(statuses),)

            path = os.path.join(self.image_path, is_in_list, username)
            self.retrieve_all(statuses, path)

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
