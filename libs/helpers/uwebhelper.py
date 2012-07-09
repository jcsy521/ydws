# -*- coding: utf-8 -*-

"""
This helper helps to pass a request to uweb. You have to prepare all the fields
a specific packet needs and the helper will pass these fields to sender via the
according url. Anyone who wants to send cwt request should use this helper, by
now, uweb, eventer use it.
"""

import hashlib
import hmac

from tornado.escape import json_encode

from constants import HTTP
from utils.dotdict import DotDict
from confhelper import ConfHelper
from basehelper import BaseHelper


class UWebHelper(object):
    # I admit that this is really ugly. Anyway, it can avoid
    # calculating the path every time.
    HOST, PATH = None, None

    # return this if the sender breaks
    DUMMY_RESPONSE = json_encode(dict(success=-1))

    URLS = DotDict(FLUSHCONFIGS=r"/flushconfigs",
                   DELEGATION=r"/delegation/5Luj5a6i5pON5L2c")

    __SECRET = "5ZOl5Lus77yM5L2g5piv5YaF6YOo5pyN5Yqh5Yi35paw55qE5ZCX77yf"

    @classmethod
    def get_sign(cls, data):
        hash_ = hmac.new(cls.__SECRET, 
                         digestmod=hashlib.md5)
        hash_.update(data)
        sign = hash_.hexdigest()
        return sign

    @classmethod
    def check_sign(cls, sign, data):
        s = cls.get_sign(data)
        if s.lower() == sign.lower():
            return True
        return False

    @classmethod
    def forward(cls, url, args, method=HTTP.METHOD.POST):
        assert ConfHelper.loaded

        return BaseHelper.forward(cls,
                                  url, args, ConfHelper.UWEB_CONF.url_in, method)
