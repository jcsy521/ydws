# -*- coding: utf-8 -*-

import logging

from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from constants import UWEB 
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from base import BaseMixin


class RemoteMixin(BaseMixin):
    """Mix-in for remote related functions."""
    
    def remote_reboot(self):
        """Reboot for terminal.
        """
        def _on_finish(response):
            status = ErrorCode.SUCCESS
            response = json_decode(response)
            if response['success'] == 0:
                pass 
            else:
                status = response['success'] 
                logging.error("Reboot failed. status: %s, message: %s", 
                               status, ErrorCode.ERROR_MESSAGE[status] )
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)

        args = DotDict(seq=SeqGenerator.next(self.db),
                       tid=self.current_user.tid)
        GFSenderHelper.async_forward(GFSenderHelper.URLS.REBOOT, args,
                                         _on_finish)
    def remote_lock(self):
        res = self.db.get("SELECT lock_status"
                          "  FROM T_TERMINAL_INFO_W"
                          "  WHERE tid = %s",
                          self.current_user.tid)

        def _on_finish(response):
            status = ErrorCode.SUCCESS
            response = json_decode(response)
            if response['success'] == 0:
                if res.lock_status == UWEB.LOCK_STATUS.YES:
                   self.db.execute("UPDATE T_TERMINAL_INFO_W"
                                   "  SET lock_status = %s",
                                   UWEB.LOCK_STATUS.NO) 
                elif res.lock_status == UWEB.LOCK_STATUS.NO:
                   self.db.execute("UPDATE T_TERMINAL_INFO_W"
                                   "  SET lock_status = %s",
                                   UWEB.LOCK_STATUS.YES) 

                else:
                    # NOTE: in fact, this branch should be never used.
                    logging.error("Unknown lock_status: %s", res.lock_status)
                    status = ErrorCode.SERVER_ERROR
            else:
                status = response['success'] 
                logging.error("Lock failed. status: %s, message: %s", 
                              status, ErrorCode.ERROR_MESSAGE[status] )
            self.write_ret(status)
            IOLoop.instance().add_callback(self.finish)

        lock_status = UWEB.LOCK_STATUS.YES
        if res.lock_status == UWEB.LOCK_STATUS.YES:
            lock_status = UWEB.LOCK_STATUS.NO

        args = DotDict(seq=SeqGenerator.next(self.db),
                       tid=self.current_user.tid,
                       lock_status=lock_status)
        GFSenderHelper.async_forward(GFSenderHelper.URLS.REMOTELOCK, args,
                                         _on_finish)

