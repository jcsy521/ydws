# -*- coding: utf-8 -*-

"""
This helper helps to communicate with sender. You have to prepare all the fields
a specific packet needs and the helper will pass these fields to sender via the
according url. Anyone who wants to send cwt request should use this helper, by
now, uweb, eventer use it.
"""

import logging

from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest, HTTPResponse
from tornado.escape import json_encode

from confhelper import ConfHelper
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict
from constants import HTTP
from basehelper import BaseHelper


class GFSenderHelper(object):
    # I admit that this is really ugly. Anyway, it can avoid
    # calculating the path every time.
    HOST, PATH = None, None

    # return this if the sender breaks
    DUMMY_RESPONSE = json_encode(dict(success=ErrorCode.SERVER_ERROR,
                                      info=ErrorCode.ERROR_MESSAGE[ErrorCode.SERVER_ERROR]))

    URLS = DotDict(REALTIME=r"/realtime",
                   TERMINAL=r"/terminal",
                   REMOTELOCK=r"/remotelock",
                   REBOOT=r"/reboot",
                   DEFEND=r"/defend",
                   QUERY=r"/query",
                   )

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
                                      ConfHelper.GF_SENDER_CONF.url,
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
            req = HTTPRequest(''.join((ConfHelper.GF_SENDER_CONF.url, url)),
                              method=HTTP.METHOD.POST,
                              headers=cls._CONTENT_TYPE,
                              body=json_encode(args),
                              connect_timeout=HTTP.ASYNC_REQUEST_TIMEOUT,
                              request_timeout=HTTP.ASYNC_REQUEST_TIMEOUT)
            cls.ASYNC_CLIENT.fetch(req, _callback)
