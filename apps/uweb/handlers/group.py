# -*- coding: utf-8 -*-

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, DUMMY_IDS_STR, str_to_list
from codes.errorcode import ErrorCode
from constants import UWEB
from base import BaseHandler, authenticated
from helpers.queryhelper import QueryHelper
from helpers.wspushhelper import WSPushHelper
       
class GroupHandler(BaseHandler):

    def get_group_by_cid(self, cid, group_name):
        #TODO:
        group = self.db.get("SELECT corp_id, name"
                            "  FROM T_GROUP"
                            "  WHERE corp_id = %s"
                            "  AND name = %s LIMIT 1",
                            cid, group_name)
        return group

    @authenticated
    @tornado.web.removeslash
    def get(self):
        """Get groups according to cid.
        """
        status = ErrorCode.SUCCESS
        try:
            res = []
            cid = self.get_argument('cid', None)
            if cid is None:
                res = []
            else:
                res = self.db.query("SELECT id AS gid, name, type"
                                    "  FROM T_GROUP"
                                    "  WHERE corp_id = %s",
                                    cid)
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] get groups failed. Exception: %s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

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
            group = self.get_group_by_cid(cid, name)
            if group:
                status = ErrorCode.GROUP_EXIST
                self.write_ret(status)
                return
            
            gid = self.db.execute("INSERT T_GROUP(id, corp_id, name, type)"
                                  "  VALUES(NULL, %s, %s, %s)",
                                  cid, name, UWEB.GROUP_TYPE.NEW)
            self.write_ret(status,
                           dict_=dict(gid=gid,
                                      cid=cid,
                                      name=name))
            #NOTE: wspush
            tid = self.current_user.tid
            if status == ErrorCode.SUCCESS:
                WSPushHelper.pushS3(tid, self.db, self.redis)
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
            cid = self.current_user.cid
            gid = data.gid
            name = data.name
            group = self.get_group_by_cid(cid, name)
            if group:
                status = ErrorCode.GROUP_EXIST
                self.write_ret(status)
                return

            self.db.execute("UPDATE T_GROUP"
                            "  SET name = %s"
                            "  WHERE id = %s",
                            name, gid)
            self.write_ret(status)
            #NOTE: wspush
            tid = self.current_user.tid
            if status == ErrorCode.SUCCESS:
                WSPushHelper.pushS3(tid, self.db, self.redis)
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
            for delete_id in delete_ids:
                terminals = self.db.query("SELECT * FROM T_TERMINAL_INFO"
                                          "  WHERE group_id = %s"
                                          "  AND (service_status = %s "
                                          "  OR service_status = %s)",
                                          delete_id, UWEB.SERVICE_STATUS.ON,
                                          UWEB.SERVICE_STATUS.TO_BE_ACTIVATED) 
                if not terminals:
                    logging.info("[UWEB] group delete request: %s, uid: %s, tid: %s", 
                                 delete_ids, self.current_user.uid, self.current_user.tid)
                    self.db.execute("DELETE FROM T_GROUP WHERE id = %s",
                                    delete_id) 
                else: 
                    status = ErrorCode.GROUP_HAS_TERMINAL
            self.write_ret(status)
            #NOTE: wspush
            tid = self.current_user.tid
            if status == ErrorCode.SUCCESS:
                WSPushHelper.pushS3(tid, self.db, self.redis)
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
                        "  WHERE tid IN %s") % (gid, tuple(tids+DUMMY_IDS_STR))
            self.db.execute(sql_cmd)
            self.write_ret(status)

            #NOTE: wspush
            tid = self.current_user.tid
            if status == ErrorCode.SUCCESS:
                WSPushHelper.pushS3(tid, self.db, self.redis)

        except Exception as e:
            logging.exception("[UWEB] cid: %s change group failed. Exception: %s", 
                              self.current_user.cid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
