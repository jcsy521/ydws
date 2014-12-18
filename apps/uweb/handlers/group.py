# -*- coding: utf-8 -*-

"""This module is designed for group.
"""

import logging

import tornado.web
from tornado.escape import json_encode, json_decode

from utils.dotdict import DotDict
from utils.misc import DUMMY_IDS, DUMMY_IDS_STR, str_to_list
from codes.errorcode import ErrorCode
from constants import UWEB
from base import BaseHandler, authenticated
from utils.public import add_group
from helpers.queryhelper import QueryHelper
from helpers.wspushhelper import WSPushHelper


class GroupHandler(BaseHandler):

    """Handle the group's information.

    :url /group
    """

    def get_group_by_cid(self, cid, group_name):
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

        #NOTE: deprecated.
        """
        status = ErrorCode.SUCCESS
        try:
            res = []
            cid = self.get_argument('cid', None)
            if not (cid is None):
                res = QueryHelper.get_groups_by_cid(cid, self.db)
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] Get groups failed. Exception: %s",
                              e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Create a new group.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] add group request: %s, cid: %s",
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. body:%s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)
            return

        try:            
            cid = data.cid
            name = data.name
            group = self.get_group_by_cid(cid, name)
            if group:
                status = ErrorCode.GROUP_EXIST
                self.write_ret(status)
                return

            group_info = dict(cid=cid,
                              name=name,
                              type=UWEB.GROUP_TYPE.NEW)
            gid = add_group(group_info, self.db, self.redis)
            # NOTE: wspush to client
            tid = self.current_user.tid
            if status == ErrorCode.SUCCESS:
                WSPushHelper.pushS3(tid, self.db, self.redis)

            self.write_ret(status,
                           dict_=dict(gid=gid,
                                      cid=cid,
                                      name=name))

        except Exception as e:
            logging.exception("[UWEB] Create group failed. uid: %s, Exception: %s",
                              self.current_user.uid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        """Modify a existing group.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            cid = self.current_user.cid
            tid = self.current_user.tid
            gid = data.gid
            name = data.name
            logging.info("[UWEB] Modify group request: %s, cid: %s",
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. body:%s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)
            return

        try:          
            group = self.get_group_by_cid(cid, name)
            if group:
                status = ErrorCode.GROUP_EXIST
                self.write_ret(status)
                return

            self.db.execute("UPDATE T_GROUP"
                            "  SET name = %s"
                            "  WHERE id = %s",
                            name, gid)

            # NOTE: wspush to client            
            if status == ErrorCode.SUCCESS:
                WSPushHelper.pushS3(tid, self.db, self.redis)

            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Modify group failed. cid: %s, Exception: %s",
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

            # NOTE: wspush to client
            tid = self.current_user.tid
            if status == ErrorCode.SUCCESS:
                WSPushHelper.pushS3(tid, self.db, self.redis)
            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Delete group failed. cid: %s, Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)


class GroupTransferHandler(BaseHandler):

    """Transfer a terminal to another group.

    :url /changegroup
    """

    @authenticated
    @tornado.web.removeslash
    def post(self):
        """Transfer some terminals to a existing group.
        """
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            logging.info("[UWEB] Transfer group request: %s, cid: %s",
                         data, self.current_user.cid)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            logging.exception("[UWEB] Invalid data format. body:%s, Exception: %s",
                              self.request.body, e.args)
            self.write_ret(status)
            return

        try:            
            tids = [str(tid) for tid in data.tids]
            gid = data.gid

            sql_cmd = ("UPDATE T_TERMINAL_INFO"
                       "  SET group_id = %s"
                       "  WHERE tid IN %s") % (gid, tuple(tids + DUMMY_IDS_STR))
            self.db.execute(sql_cmd)

            # NOTE: wspush to client
            tid = self.current_user.tid
            if status == ErrorCode.SUCCESS:
                WSPushHelper.pushS3(tid, self.db, self.redis)

            self.write_ret(status)
        except Exception as e:
            logging.exception("[UWEB] Transfer group failed. cid: %s, Exception: %s",
                              self.current_user.cid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
