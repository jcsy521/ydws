# -*- coding: utf-8 -*-

import redis

from dotdict import DotDict
from helpers.confhelper import ConfHelper


class MyRedis(redis.Redis):

    def __init__(self, **kwargs):
        assert ConfHelper.loaded
        host = ConfHelper.REDIS_CONF.host
        port = int(ConfHelper.REDIS_CONF.port)
        redis.Redis.__init__(self, host=host, port=port)

    def setvalue(self, key, value, time=None):
        if isinstance(value, DotDict):
            value = dict(value)
        self.set(key, value)
        if time:
            self.expire(key, time)

    def getvalue(self, key):
        value = self.get(key)
        if value:
            try:
                e_value = eval(value)
                if isinstance(e_value, dict):
                    e_value = DotDict(e_value)
                return e_value
            except:
                return value
        else:
            return None
