import json
from redis import Redis
from oel.settings import REDIS_HOST

# rd = Redis(REDIS_HOST)

rd = {}


def set(key, value, expire=86400):

    if isinstance(value, dict):
        value = json.dumps(value, cls=JSONEncoder)

    rd[key] = value


def get(key):

    return rd[key]


def delete(key):

    rd[key] = None
    return True


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'strftime'):
            return obj.strftime('%m/%d/%Y')
        return obj
