# -*- coding: UTF-8 -*-

import logging
import time

import tornado.web
from tornado.escape import  json_decode  

from helpers.emailhelper import EmailHelper 
from utils.dotdict import DotDict
from utils.misc import str_to_list, DUMMY_IDS
from codes.errorcode import ErrorCode
from base import authenticated,BaseHandler

class FeedBackHandler(BaseHandler):
    
    @authenticated
    def get(self):
        """Jump to feedback.html
        """
        username = self.get_current_user()
        n_role = self.db.get("SELECT role FROM T_LOG_ADMIN WHERE name = %s", username)
        self.render("feedback/feedback.html",
                     username=username, 
                     role=n_role.role)

    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            logging.info("[LOG] Feedback request: %s", data)
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            isreplied = data.get("isreplied", -1)
        except Exception as e:
            logging.info("[LOG] Feedback illegal data format. Exception: %s", e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)

        try: 
            if isreplied == -1: # all reply
                res = self.acbdb.query("SELECT id, contact, email, content, timestamp, reply, reply_time, isreplied, category"
                                       "  FROM T_FEEDBACK"
                                       "  WHERE timestamp BETWEEN %s AND %s"
                                       "  ORDER BY timestamp DESC",
                                       start_time, end_time)

            else:
                res = self.acbdb.query("SELECT id, contact, email, content, timestamp, reply, reply_time, isreplied, category"
                                       "  FROM T_FEEDBACK"
                                       "  WHERE timestamp BETWEEN %s AND %s AND isreplied = %s "
                                       "  ORDER BY timestamp DESC",
                                       start_time, end_time, isreplied)
            self.write_ret(status,
                           dict_=DotDict(res=res))
        except Exception as e: 
            logging.exception("[LOG] Feedback query failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def put(self):
        status = ErrorCode.SUCCESS
        try:
            data = json_decode(self.request.body)
            logging.info("data: %s", data)
            id = data.get("id", -1)
            reply = data.get("reply","")
            email = data.get("email", "")
        except Exception as e:
            logging.info("[LOG] Feedback illegal data format. Exception: %s", e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)

        try: 
            reply_time = int(time.time())
            self.acbdb.execute("UPDATE T_FEEDBACK"
                               "  SET reply = %s,"
                               "     reply_time = %s"
                               "  WHERE id = %s",
                               reply, reply_time, id)
            # if email is not null, send email to user
            if email: 
                self.acbdb.execute("UPDATE T_FEEDBACK"
                                   "  SET isreplied = 1"
                                   "  WHERE id = %s",
                                   id)
                body = u"尊敬的客户：\n\t首先感谢您对【移动卫士】的支持与关心，对您的意见反馈表示衷心感谢。\n\t针对您的反馈内容，工作人员做了如下回复：\n\t%s\n\n\t【移动卫士】" % reply 
                EmailHelper.send(email, body, [], []) 
            self.write_ret(status,
                           dict_=DotDict(reply_time=reply_time))
        except Exception as e: 
            logging.exception("[LOG] Feedback query failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

    @authenticated
    @tornado.web.removeslash
    def delete(self):
        status = ErrorCode.SUCCESS
        try:
            delete_ids = map(int, str_to_list(self.get_argument('ids', None)))
        except Exception as e:
            logging.info("[LOG] Feedback illegal data format. Exception: %s", e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)

        try: 
            self.acbdb.execute("DELETE FROM T_FEEDBACK"
                               "  WHERE id IN %s",
                               tuple(delete_ids + DUMMY_IDS))
            self.write_ret(status)
        except Exception as e: 
            logging.exception("[LOG] Feedback query failed. Exception: %s", e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
     
        
