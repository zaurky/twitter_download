#!/usr/bin/python

from download_twitter.config import get_config
from download_twitter.twitter import Twitter


if __name__ == '__main__':
    TWITTER = Twitter(get_config())
    TWITTER.refresh_friend()
    TWITTER.refresh_lists()
    friends = TWITTER.friends.keys()
    for list_name, content in TWITTER.listcontent['list_content'].items():
        for friend_id in content:
            if friend_id not in friends:
                print "friend %s not in friend list" % friend_id
            else:
                friends.remove(friend_id)

    print "friends in not group : "
    print ", ".join([TWITTER.friends[fid] for fid in friends])
