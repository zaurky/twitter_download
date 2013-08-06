#!/usr/bin/python

import ConfigParser, os
from download_twitter.api import API
from download_twitter.cache import FriendList, ListContent


def get_list_content(api):
    """
    Get list content and friends in list
    """
    list_content = {}
    friend_in_list = {}

    for list_id, list_name in api.get_lists():
        friends = api.get_list_users(list_id)
        list_content[list_name] = friends
        friend_in_list.update(
                dict([(friend_id, list_name) for friend_id in friends]))
    return {
        'list_content': list_content,
        'friend_in_list': friend_in_list,
    }


if __name__ == '__main__':
    CONFIG = ConfigParser.ConfigParser()
    CONFIG.read(['/etc/twitter_image.conf',
                 'twitter_image.conf',
                 os.path.expanduser('~/.twitter_image.conf')])

    API = API(CONFIG)

    FRIENDLIST = FriendList(CONFIG)
    for key, value in API.get_friends():
        FRIENDLIST[key] = value

    LISTCONTENT = ListContent(CONFIG)
    for key, value in get_list_content(API).items():
        LISTCONTENT[key] = value
