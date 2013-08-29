#!/usr/bin/python
"""
Utils functions
"""


def sanitize(string):
    """ Remove all non ascii chars to be able to put the string in exif """
    return unicode(string).encode('ascii', 'replace')


## status treatments
def is_retweet(status):
    """ says if a status is a retweet or not """
    return ('retweeted_status' in status
            and status['retweeted_status']['user']['screen_name']
                != status['user']['screen_name'])


def simplify_status(status):
    """ only get the information we use from a status """
    ret = {
        'created_at': status['created_at'],
        'id': status['id'],
        'text': status['text'],
        'user': {
            'screen_name': status['user']['screen_name'],
            'name': status['user']['name'],
        },
    }
    if 'media' in status['entities']:
        ret['entities'] = {
            'media': status['entities']['media'],
        }
    ret['restatus'] = is_retweet(status)
    return ret


def get_images_from_status(status):
    """ Extract medias from a twitter status """
    return [(media['id_str'], media['media_url'])
            for media in status['entities'].get('media', [])]
