#!/usr/bin/python

from download_twitter.config import get_config
from download_twitter.twitter import Twitter
from download_twitter.exception import RateLimit


def main(twitter):
    twitter.refresh_friend()
    twitter.refresh_lists()
    friends = twitter.friends.keys()
    for _, content in twitter.listcontent['list_content'].items():
        for friend_id in content:
            if friend_id not in friends:
                print "friend %s not in friend list" % friend_id
            else:
                friends.remove(friend_id)

    print "friends in not group : "
    print ", ".join([twitter.friends[fid] for fid in friends])


if __name__ == '__main__':
    TWITTER = Twitter(get_config())
    try:
        main(TWITTER)
    except RateLimit:
        print "Ratelimited"
