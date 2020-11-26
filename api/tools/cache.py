import json
from redis import Redis
from oel.settings import REDIS_HOST

rd = Redis(REDIS_HOST)


def set(key, value, expire=86400):

    if isinstance(value, dict):
        value = json.dumps(value, cls=JSONEncoder)

    rd.set(key, value, expire)


def get(key):

    return rd.get(key)


def delete(key):

    return rd.delete(key)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'strftime'):
            return obj.strftime('%m/%d/%Y')
        if isinstance(obj, ObjectId):
            return str(obj)
        return obj
