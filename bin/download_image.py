#!/usr/bin/python

from download_twitter.image import Twitter
import ConfigParser, os


if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read(['/etc/twitter_image.conf',
                 'twitter_image.conf',
                 os.path.expanduser('~/.twitter_image.conf')])

    twitter = Twitter(config)
    twitter.run()
