# -*- coding: utf-8 -*-

import httplib
import urlparse

from tornado.escape import json_encode

from constants import HTTP


class BaseHelper(object):
    # override this value in subclass if necessary.
    # HOST, PATH = None, None
    # DUMMY_RESPONSE = json_encode(dict(success=-1))

    @staticmethod
    def forward(cls, url, args, base_url, method=HTTP.METHOD.POST):
        """Forward the info packet to url.
        
        @param cls: HOST, PATH are stored seperatly for subclasses, and
        it's necessary to tell them apart here.
        """
        assert cls is not BaseHelper
        
        if cls.HOST is None:
            r = urlparse.urlparse(base_url)
            cls.HOST = r.netloc
            if r.path.endswith('/'):
                cls.PATH = r.path[:-1]
            else:
                cls.PATH = r.path

        try:
            connection = httplib.HTTPConnection(cls.HOST,
                                                timeout=HTTP.ASYNC_REQUEST_TIMEOUT)
            params = json_encode(args)
            headers = {"Content-type": "application/json; charset=utf-8"}
            full_path = cls.PATH + url if url else cls.PATH
            connection.request(method, full_path, params, headers)
            response = connection.getresponse()
            # TODO: the server returns something useful
            if response.status == 200:
                ret = response.read()
            else:
                ret = cls.DUMMY_RESPONSE
            connection.close()
        except:
            # can not communicate with sender. mimic the error return
            # from sender.
            ret = cls.DUMMY_RESPONSE
        return ret
