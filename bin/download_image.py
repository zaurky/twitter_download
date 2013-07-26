#!/usr/bin/python

from download_twitter.image import Twitter
import ConfigParser, os


if __name__ == '__main__':
    CONFIG = ConfigParser.ConfigParser()
    CONFIG.read(['/etc/twitter_image.conf',
                 'twitter_image.conf',
                 os.path.expanduser('~/.twitter_image.conf')])

    TWITTER = Twitter(CONFIG)
    TWITTER.run()
