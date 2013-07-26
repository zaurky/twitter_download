#!/usr/bin/python

from download_twitter.image import Twitter
import ConfigParser, os


if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read(['/etc/twitter_image.conf',
                 'twitter_image.conf',
                 os.path.expanduser('~/.twitter_image.conf')])

    twitter = Twitter(
                config.get('main', 'consumer_key'),
                config.get('main', 'consumer_secret'),
                config.get('main', 'access_key'),
                config.get('main', 'access_secret'))

    twitter.run()
