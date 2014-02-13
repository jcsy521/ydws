# -*- coding: utf-8 -*-

import time
import logging

from tornado.escape import json_encode

from base import BaseHandler, authenticated
from helpers.queryhelper import QueryHelper
from helpers.confhelper import ConfHelper
from constants import UWEB, GATEWAY
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict

class MainHandler(BaseHandler):

    # BIG NOTE: never add removeslash decorator here!
    @authenticated
    def get(self):
        status=ErrorCode.SUCCESS
        from_ = self.get_argument('from', '').lower()
        index_html = "index.html"
        bizcode = None
        name = ''
        if self.current_user.oid != UWEB.DUMMY_OID:
            index_html = "index_corp.html"
            umobile=self.current_user.oid
            user_info = QueryHelper.get_operator_by_oid(self.current_user.oid, self.db)
            corp_info = QueryHelper.get_corp_by_oid(self.current_user.oid, self.db)
            if user_info:
                name = user_info.name if user_info.name else user_info.mobile 
            user_type = UWEB.USER_TYPE.OPERATOR
            bizcode = corp_info.bizcode
        elif self.current_user.cid != UWEB.DUMMY_CID:
            index_html = "index_corp.html"
            umobile=self.current_user.cid
            user_info = QueryHelper.get_corp_by_cid(self.current_user.cid, self.db)
            if user_info:
                name = user_info.linkman if user_info.linkman else user_info.mobile 
            user_type = UWEB.USER_TYPE.CORP
            bizcode = user_info.bizcode
        else:
            umobile=self.current_user.uid
            user_info = QueryHelper.get_user_by_uid(self.current_user.uid, self.db)
            if user_info:
                name = user_info.name if user_info.name else user_info.mobile 
            user_type = UWEB.USER_TYPE.PERSON

        if not user_info:
            status = ErrorCode.LOGIN_AGAIN
            logging.error("The user with uid: %s does not exist, redirect to login.html", self.current_user.uid)
            self.render("login.html",
                        username='',
                        password='',
                        user_type=UWEB.USER_TYPE.PERSON,
                        message=None,
                        message_captcha=None)
            return

        self.render(index_html,
                    map_type=ConfHelper.LBMP_CONF.map_type,
                    user_type=user_type,
                    bizcode=bizcode,
                    status=status,
                    name=name,
                    umobile=umobile)
