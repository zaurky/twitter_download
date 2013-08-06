#!/usr/bin/python

from download_twitter.config import get_config
from download_twitter.twitter import Twitter


if __name__ == '__main__':
    TWITTER = Twitter(get_config())
    TWITTER.refresh_friend()
    TWITTER.refresh_lists()
