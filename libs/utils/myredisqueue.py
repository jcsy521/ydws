# -*- coding: utf-8 -*-

import redis
from helpers.confhelper import ConfHelper


class MyRedisQueue(object):

    """Simple Queue with Redis Backend"""

    def __init__(self, name, namespace='queue', **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.name = name
        host = ConfHelper.REDIS_CONF.host
        port = int(ConfHelper.REDIS_CONF.port)
        password = ConfHelper.REDIS_CONF.password
        self.__redis = redis.Redis(host=host, port=port, password=password, db=0)
        self.key = '%s:%s' % (namespace, name)

    
    @property
    def name(self):
        """
        """
        return self.name
    @property
    def size(self):
        """Return the approximate size of the queue."""
        return self.__redis.llen(self.key)
    
    @property
    def is_empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put the item into the queue."""
        self.__redis.rpush(self.key, item)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue. 

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available.

        #NOTE: If 
        #NOTE: If nothing can be found from the queue, None will be got through lpop() method.
        """
        if block:
            item = self.__redis.blpop(self.key, timeout=timeout)
        else:
            item = self.__redis.lpop(self.key)
        return item

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)
