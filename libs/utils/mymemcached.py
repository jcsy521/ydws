# -*- coding: utf-8 -*-

import memcache

from helpers.confhelper import ConfHelper

class MyMemcached(memcache.Client):
    def __init__(self, **kwargs):
        assert ConfHelper.loaded
        host1 = ConfHelper.MEMCACHED_CONF.host1
        uri = [host1,] 
        memcache.Client.__init__(self, uri, **kwargs)
