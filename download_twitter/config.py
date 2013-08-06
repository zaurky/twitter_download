# -*- coding: utf-8 -*-
"""
The download_twitter config module
"""

import ConfigParser, os


def get_config():
    """ Get the configuration """
    config = ConfigParser.ConfigParser()
    config.read(['/etc/twitter_image.conf',
                 'twitter_image.conf',
                 os.path.expanduser('~/.twitter_image.conf')])
    return config
