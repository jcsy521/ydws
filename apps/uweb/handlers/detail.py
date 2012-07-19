# -*- coding: utf-8 -*-

import logging
import datetime
import time
from dateutil.relativedelta import relativedelta

from tornado.escape import json_decode, json_encode
import tornado.web

from helpers.seqgenerator import SeqGenerator
#from helpers.gfsenderhelper import GFSenderHelper
#from helpers.queryhelper import QueryHelper
from utils.misc import get_today_last_month
from utils.dotdict import DotDict
#from constants import QUERY

from base import BaseHandler, authenticated
from codes.errorcode import ErrorCode


class DetailHandler(BaseHandler):
    """Browse location fixes from Web."""

    @authenticated
    @tornado.web.removeslash
    def get(self):
        data = self.db.get("SELECT T_USER.id, mobile, name, address, email, corporation, remark, cid"
                           "  FROM T_USER, T_CAR"
                           "  WHERE T_CAR.uid = %s"
						   "    AND T_CAR.tid = %s"
						   "    AND T_USER.uid = T_CAR.uid",
                           self.current_user.uid, self.current_user.tid)
        self.write_ret(ErrorCode.SUCCESS,
                       dict_=dict(id=data.id,
                                  details=(dict(name=data.name,
                                                mobile=data.mobile,
                                                address=data.address,
                                                email=data.email,
                                                corporation=data.corporation,
                                                remark=data.remark,
												cid=data.cid))))

    @authenticated
    @tornado.web.removeslash
    def put(self):
        try:
            data = DotDict(json_decode(self.request.body))
            name = data.name
            mobile = data.mobile
            address= data.address
            email = data.email
            corporation = data.corporation
            remark = data.remark
            id = data.id
            cid = data.cid
			
            self.db.execute("UPDATE T_USER"
                            "  SET mobile = %s,"
                            "      name = %s,"
                            "      address = %s,"
                            "      email = %s,"
                            "      corporation = %s,"
                            "      remark = %s"
                            "  WHERE id = %s",
                            mobile, name, address, email, corporation, remark, id)
            self.db.execute("UPDATE T_CAR"
                            "  SET cid = %s"                                                                 
                            "  WHERE uid = %s"
                            "    AND tid = %s",
                            cid, self.current_user.uid, self.current_user.tid)
            self.write_ret(ErrorCode.SUCCESS)

        except Exception as e:
            logging.exception("Update detail failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

