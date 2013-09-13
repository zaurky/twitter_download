# -*- coding: utf-8 -*-

from download_twitter.api import API
from download_twitter.cache import (LastId,
                                    FriendList,
                                    ListContent,
                                    WeightFriends,
                                    Ratelimit,
                                    DeletedFriends)
from download_twitter.config import get_config


CONFIG = get_config()
api = API(CONFIG)


def getLastId():
    return LastId(CONFIG)


def getFriendList():
    return FriendList(CONFIG)


def getWeightList():
    return WeightFriends(CONFIG)


def getListContent():
    return ListContent(CONFIG)


def getRatelimit():
    return Ratelimit(CONFIG)


def getDeletedFriends():
    return DeletedFriends(CONFIG)


def refreshFriendList():
    friends = getFriendList()
    for key, value in api.get_friends():
        friends[key] = value


def refreshListContent():
    listcontent = getListContent()
    for key, value in api.retrieve_list_content().items():
        listcontent[key] = value


def rmList(user_name):
    rss_id, _list_name = api.get_list(list_name='Rss')
    rss = dict(api.get_list_users(rss_id))

    person_id, _list_name = api.get_list(list_name='Person')
    person = dict(api.get_list_users(person_id))

    friend_id, friend_name = api.get_friend(user_name=user_name)
    if friend_id in rss:
        api.del_user_from_list('Rss', friend_name)
    elif friend_id in person:
        api.del_user_from_list('Person', friend_name)
    else:
        print "%s is not in a list" % user_name


def setRss(user_name):
    return api.put_user_in_list('Rss', user_name)


def setPerson(user_name):
    return api.put_user_in_list('Person', user_name)


def info(user_name):
    return api.get_friend(user_name=user_name)


def show_ratelimit():
    ratelimit = getRatelimit()
    dft_ratelimit = dict([(k, int(v))for k, v in CONFIG.items('ratelimit')])

    ret = {}
    now = api.twitter.now()
    for url, limit in dft_ratelimit.items():
        total = 0
        for date in range(now - 16, now):
            total += ratelimit[url].get(date, 0)
        ret[url] = [limit, total]
    return ret
