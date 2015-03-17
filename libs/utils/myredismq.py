# -*- coding: utf-8 -*-

import logging
import redis
import json
from helpers.confhelper import ConfHelper


class MyRedisMQ(object):

    """Simple Queue with Redis Backend

    The methods is like build_in queue.

    In put method, push item in right. In get method, pop item in left.
    It works FIFO queue.

    """

    def __init__(self, name, namespace='queue', **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.name = name
        host = ConfHelper.REDIS_CONF.host
        port = int(ConfHelper.REDIS_CONF.port)
        # password = ConfHelper.REDIS_CONF.password
        # self.__redis = redis.Redis(host=host, port=port, password=password, db=0)
        self.__redis = redis.Redis(host=host, port=port, db=0)
        self.key = '%s:%s' % (namespace, self.name)
   
    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__redis.llen(self.key)
    
    @property
    def is_empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put the item into the queue."""
        
        # add it
        logging.info("[MYREDISMQ] Put item in mq:%s, name:%s, item: %s", 
                     self, self.name,  item)
        item = json.dumps(item)

        self.__redis.rpush(self.key, item)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue. 

        :return item: python object.


        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available.

        #NOTE: blpop method return a tuple. lpop return a item.
        #NOTE: If nothing can be found from the queue, None will be got through lpop() method.
        """
        # return None
        if block:      
            item = self.__redis.blpop(self.key, timeout=timeout)[-1]
        else:
            item = self.__redis.lpop(self.key)

        if item:
            item = json.loads(item)
        else:
            item = None
        return item

    def close(self):
        """Do nothing.
        """
        pass

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)
