# -*- coding: utf-8 -*-

"""
This helper helps to pass a request to uweb. You have to prepare all the fields
a specific packet needs and the helper will pass these fields to sender via the
according url. Anyone who wants to send cwt request should use this helper, by
now, uweb, eventer use it.
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
        m=hashlib.md5() 
        m.update(password)
        hash_=m.hexdigest()
        m.update(hash_+timestamp)
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
    def get_token(cls, redis):
        """Generate a token.
        """
        token = get_token()
        redis.setvalue(token, True, time=OPENAPI.TOKEN_EXPIRES)
        return token
    
    @classmethod
    def check_token(cls, token, redis):
        """Check whether the token is valid.
        """
        is_existed = redis.get(token)
        if is_existed: 
            return True
        else:
            return False 
