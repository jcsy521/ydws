# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, DUMMY_IDS_STR, get_terminal_info_key, get_location_key, str_to_list
from codes.errorcode import ErrorCode
from helpers.queryhelper import QueryHelper
from constants import UWEB, EVENTER, GATEWAY
from constants.MEMCACHED import ALIVED
from base import BaseHandler, authenticated

       
class GroupHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Create a new group.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] add group request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            cid = data.cid
            name = data.name
            gid = self.db.execute("INSERT T_GROUP(id, corp_id, name, type)"
                                  "  VALUES(NULL, %s, %s, %s)",
                                  cid, name, UWEB.GROUP_TYPE.NEW)
            self.write_ret(status,
                           dict_=dict(gid=gid,
                                      cid=cid,
                                      name=name))
        except Exception as e:
            logging.exception("[UWEB] uid: %s create group failed. Exception: %s", 
                              self.current_user.uid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify a existing group.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] modify group request: %s, cid: %s", 
                         data, self.current_user.cid)

        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            gid = data.gid
            name = data.name
            self.db.execute("UPDATE T_GROUP"
                            "  SET name = %s"
                            "  WHERE id = %s",
                            name, gid)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s modify group failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        """Delete a group.
        """
        try:
            status = ErrorCode.SUCCESS
            delete_ids = map(int, str_to_list(self.get_argument('ids', None)))
            logging.info("[UWEB] group delete request: %s, uid: %s, tid: %s", 
                         delete_ids, self.current_user.uid, self.current_user.tid)
            self.db.execute("DELETE FROM T_GROUP WHERE id IN %s",
                            tuple(delete_ids+DUMMY_IDS)) 
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s delete group failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class GroupTransferHandler(BaseHandler):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Tranfer some terminals to a existing group.
        """
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] change group request: %s, cid: %s", 
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        try:
            status = ErrorCode.SUCCESS
            tids = [str(tid) for tid in data.tids]
            gid = data.gid
            sql_cmd  = ("UPDATE T_TERMINAL_INFO"
                        "  SET group_id = %s"
                        "  WHERE tid IN %s") % (gid, tuple(tids+DUMMY_IDS))
            self.db.execute(sql_cmd)

            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] cid: %s change group failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
