#!/usr/bin/python

from download_twitter.config import get_config
from download_twitter.twitter import Twitter


def main():
    API = Twitter(get_config())
    count = API.cache_all_friends_tweets()
    print "%d friends treated" % count


if __name__ == '__main__':
    main()
