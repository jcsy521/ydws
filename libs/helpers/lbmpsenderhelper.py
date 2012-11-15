# -*- coding: utf-8 -*-

import httplib
import logging

from tornado.escape import json_encode
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest, HTTPResponse

from confhelper import ConfHelper
from basehelper import BaseHelper
from codes.errorcode import ErrorCode
from constants import HTTP
from utils.dotdict import DotDict

class LbmpSenderHelper(object):
    """ 
    /le: cellid
    /gv: get location_name
    /ge: convert longitude and latitude
    /gv_query: query the POI from LBMP
    """

    HOST, PATH = None, None
    DUMMY_RESPONSE = json_encode(dict(success=ErrorCode.SERVER_ERROR,
                                      info=ErrorCode.ERROR_MESSAGE[ErrorCode.SERVER_ERROR]))

    URLS = DotDict(LE=r"/le",
                   SUBSCRIPTION=r"/subscription",
                   GV=r"/gv",
                   GV_QUERY=r"/gv_query",
                   GE=r"/ge")

    _CONTENT_TYPE = {"Content-type": "application/json; charset=utf-8"}

    ASYNC_CLIENT = AsyncHTTPClient(max_clients=500)

    @classmethod
    def forward(cls, url, args, method=HTTP.METHOD.POST):
        """Forward the request in block most (sync mode) to sender.

        This means I will wait for the response from sender, which would block
        following requests. This should be avoided in uweb.
        """
        assert ConfHelper.loaded
        if method.upper() not in HTTP.METHOD:
            return cls.DUMMY_RESPONSE
        else:
            args['method'] = method.upper()
            return BaseHelper.forward(cls,
                                      url,
                                      args,
                                      ConfHelper.LBMP_SENDER_CONF.url,
                                      HTTP.METHOD.POST)

    @classmethod
    def async_forward(cls, url, args, callback, method=HTTP.METHOD.POST):
        """Forward a single request to sender in non-blocking mode (async mode).

        This leverage the AsyncHTTPClient of tornado. The request will return
        immediately so that following requests can be processed. callback() is
        passed to handle the response from sender. Note that, the response is an
        HTTPResponse object.
        """
        assert ConfHelper.loaded

        def _callback(response):
            if isinstance(response, HTTPResponse) and response.error is None:
                callback(response.body)
            elif isinstance(response, HTTPResponse) and response.error and response.error.code == 599:
                callback(json_encode(dict(success=ErrorCode.TERMINAL_TIME_OUT,
                                          info=ErrorCode.ERROR_MESSAGE[ErrorCode.TERMINAL_TIME_OUT])))
            else:
                callback(cls.DUMMY_RESPONSE)

        if method.upper() not in HTTP.METHOD:
            _callback(None)
        else:
            args['method'] = method.upper()
            req = HTTPRequest(''.join((ConfHelper.LBMP_SENDER_CONF.url, url)),
                              method=HTTP.METHOD.POST,
                              headers=cls._CONTENT_TYPE,
                              body=json_encode(args),
                              connect_timeout=HTTP.ASYNC_REQUEST_TIMEOUT,
                              request_timeout=HTTP.ASYNC_REQUEST_TIMEOUT)
            cls.ASYNC_CLIENT.fetch(req, _callback)

