# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_decode, json_encode
from tornado.ioloop import IOLoop

from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper
from utils.misc import DUMMY_IDS, str_to_list, get_today_last_month
from utils.dotdict import DotDict
from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode
from constants import UWEB
from mixin.terminallist import TerminalListMixin


class TerminalListHandler(BaseHandler, TerminalListMixin):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            tlist = [DotDict(item) for item in json_decode(self.request.body)]
            res = self.get_terminallist(self.current_user.uid) 
            if len(res) + len(tlist) > UWEB.LIMIT.TERMINAL: 
                self.write_ret(ErrorCode.ADDITION_EXCESS)
                return 
            ids = []
            for item in tlist:
                ids.append(DotDict(status=ErrorCode.FAILED, id=item.id))
            last_rowid = self.insert_terminal(tlist)
            # if last_rowid returns None, it denotes there is an error on database operation. 
            if last_rowid:
                # we assume executemany is an atomic operation
                id_list = range((last_rowid - len(tlist) + 1), (last_rowid + 1))
                for i, id in enumerate(id_list): 
                    ids[i].status = ErrorCode.SUCCESS
                    ids[i].id = id
            else:
                logging.error("[UWEB] Error: Database error, tid: %s", self.current_user.tid)
        except Exception as e:         
            logging.exception("[UWEB] Add terminal failed. Exception: %s", e.args)
            self.write_ret(ErrorCode.SERVER_ERROR)
            return
        self.write_ret(status, dict_=DotDict(ids=ids))

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Broken the relation between user and terminal."""
        status = ErrorCode.SUCCESS
        try:
            ids = []
            delete_ids = map(int, str_to_list(self.get_argument('ids', None)))
            if not delete_ids: 
                self.write_ret(ErrorCode.ILLEGAL_DATA_FORMAT)
                return 
            for item in delete_ids:
                ids.append(DotDict(status=ErrorCode.SUCCESS,id=item))
                self.delete_terminal(delete_ids)
        except Exception as e:         
            logging.exception("[UWEB] Delete terminal failed. Exception: %s", e.args)
            self.write_ret(ErrorCode.SERVER_ERROR)
            return
        self.write_ret(status, dict_=DotDict(ids=ids))
