# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB 
from base import BaseHandler, authenticated
from mixin.remote import RemoteMixin

class RemoteHandler(BaseHandler, RemoteMixin):
    """
    Handler for REBOOT, LOCK events.
    """
    @authenticated
    @tornado.web.removeslash
    @tornado.web.asynchronous
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            command = data.get('action')
            if command not in UWEB.REMOTE_EVENT_COMMAND:
                status = ErrorCode.UNKNOWN_COMMAND
            else:
                if command == UWEB.REMOTE_EVENT_COMMAND.REBOOT:
                    self.remote_reboot()

                elif command == UWEB.REMOTE_EVENT_COMMAND.LOCK:
                    self.remote_lock()
                    
        except Exception as e:
            logging.exception("Remote failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_ERROR
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)
