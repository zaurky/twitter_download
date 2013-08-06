#!/usr/bin/python

import ConfigParser, os
from download_twitter.twitter import Twitter


if __name__ == '__main__':
    CONFIG = ConfigParser.ConfigParser()
    CONFIG.read(['/etc/twitter_image.conf',
                 'twitter_image.conf',
                 os.path.expanduser('~/.twitter_image.conf')])

    TWITTER = Twitter(CONFIG)
    TWITTER.refresh_friend()
    TWITTER.refresh_lists()
