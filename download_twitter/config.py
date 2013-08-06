# -*- coding: utf-8 -*-

import ConfigParser, os


def get_config():
    config = ConfigParser.ConfigParser()
    config.read(['/etc/twitter_image.conf',
                 'twitter_image.conf',
                 os.path.expanduser('~/.twitter_image.conf')])
    return config
