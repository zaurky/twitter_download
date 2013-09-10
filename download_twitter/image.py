#!/usr/bin/python
"""
Image module
"""

import pexif
from pexif import JpegFile

from .utils import sanitize, is_retweet, get_images_from_status

import os
from distutils.dir_util import mkpath
from datetime import datetime


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

    OK = 0
    RETWEET = 1
    EMPTY = 2
    EXISTS = 3
    RETWEET_EXISTS = 4

    def retrieve_image(self, media_id, media_url, status):
        """ Retrieve the image """
        retweet = self._retweet if is_retweet(status) else ''
        filepath = os.path.join(self.path, retweet, media_id + '.jpg')
        if not self.should_get_image(media_url, filepath):
            return self.RETWEET_EXISTS if retweet else self.EXISTS

        data = self._api.get_image(media_url)
        if not data:
            return self.EMPTY

        self.prepare_dir(filepath)
        Image(media_id, filepath, data, status).write()
        self.link_daily(filepath)
        return self.RETWEET if retweet else self.OK

    def retrieve_all(self, statuses):
        """ loop over all the statuses and call `retrieve_image` on each """
        pic_nb = 0
        retweet_nb = 0
        for status in statuses:
            for media_id, media_url in get_images_from_status(status):
                state = self.retrieve_image(media_id, media_url, status)
                if state in (self.OK, self.RETWEET):
                    pic_nb += 1
                if state in (self.RETWEET, ):
                    retweet_nb += 1

        return pic_nb, retweet_nb
