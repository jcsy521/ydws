# -*- coding: utf-8 -*-

"""This helper helps to check the requests in openapi.
"""

import hashlib

from tornado.escape import json_encode

from constants import OPENAPI
from utils.openapi_misc import get_token


class OpenapiHelper(object):

    @classmethod
    def get_sign(cls, password, timestamp):
        """Generate a sign.
        md5(md5(password)+timestamp)
        """
        m = hashlib.md5()
        m.update(password)
        hash_ = m.hexdigest()
        m.update(hash_ + timestamp)
        sign = m.hexdigest()   
        return sign

    @classmethod
    def check_sign(cls, sign, password, timestamp):
        """Check whether the sign is valid.
        """
        s = cls.get_sign(password, timestamp)
        if s.lower() == sign.lower():
            return True
        return False

    @classmethod
    def get_token(cls, redis, sp):
        """Generate a token and keep it in redis.
        """
        token = 'OPENAPI%s' % get_token()
        redis.setvalue(token, sp, time=OPENAPI.TOKEN_EXPIRES)
        return token

    @classmethod
    def check_token(cls, redis, token):
        """Check whether the token is valid.
        """
        sp = redis.getvalue(token)
        return sp       
