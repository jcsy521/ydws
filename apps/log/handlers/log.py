# -*- coding: UTF-8 -*-

import logging

import tornado.web
from tornado.escape import  json_decode  

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from base import authenticated,BaseHandler

class Log(BaseHandler):
    
    @authenticated
    def get(self):

        username = self.get_current_user()
        n_role = self.db.get("select role from T_LOG_ADMIN where name = %s", username)
        self.render("log/log.html",
                     username=username,
					 role = "")
        return

    @authenticated
    @tornado.web.removeslash
    def post(self):
        try:
            data = json_decode(self.request.body)
            start_time = data.get("start_time")
            end_time = data.get("end_time")
            plan_id = data.get("plan_id")
            level = data.get("level")
        except Exception as e:
            #TODO: 
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return

        if level:
            if  start_time:
                try:
                    if plan_id:
                        allLog = self.db.query("SELECT id, level, servername, details,"
                                               "  DATE_FORMAT(time, '%%Y-%%m-%%d %%H:%%i:%%s')"
                                               "  AS  time FROM T_LOG_DETAILS"
                                               "    WHERE servername = %s"
                                               "      AND time BETWEEN %s AND %s"
                                               "      AND level = %s",
                                               plan_id, start_time, end_time, level)
                        self.write_ret(ErrorCode.SUCCESS,
                                       dict_=DotDict(log_list=allLog))
                    else:
                        allLog = self.db.query("SELECT id, level, servername, details,"
                                               "  DATE_FORMAT(time,'%%Y-%%m-%%d %%H:%%i:%%s')"
                                               "  AS time FROM T_LOG_DETAILS"
                                               "    WHERE time BETWEEN %s AND %s"
                                               "    AND level = %s",
                                               start_time, end_time, level)
                        self.write_ret(ErrorCode.SUCCESS,
                                       dict_=DotDict(log_list=allLog))
                except Exception as e:
                    # TODO: remvoe unwanted dict_
                    logging.exception("[LOG] Log's inquiry failed. Inquiry condition:"
                                      "start_time: %s"
                                      "end_time: %s"
                                      "plan_id: %s"
                                      "level: %s"
                                      "Exception: %s",
                                      start_time, end_time, plan_id, level, e.args)
                    self.write_ret(ErrorCode.FAILED)
            else:#if time is null
                self.render("log/log.html",
                            allLog={},
                            start_time="",
                            end_time="",
                            plan_id="",
                            level="",
                            username=None,)
                return
        else:
            if  start_time:#have time's value
                try:
                    if plan_id:#have the plan_id value  try:    except
                        allLog = self.db.query("SELECT id, level, servername, details,"
                                               "  DATE_FORMAT(time,'%%Y-%%m-%%d %%H:%%i:%%s')"
                                               "  AS time FROM T_LOG_DETAILS"
                                               "    where servername=%s"
                                               "    AND time BETWEEN %s AND %s",
                                               plan_id, start_time, end_time)
                        self.write_ret(ErrorCode.SUCCESS,
                                       dict_=DotDict(log_list=allLog))
                    else:
                        allLog = self.db.query("SELECT id, level, servername, details,"
                                               "  DATE_FORMAT(time,'%%Y-%%m-%%d %%H:%%i:%%s')"
                                               "  AS time FROM T_LOG_DETAILS "
                                               "    WHERE time BETWEEN %s AND %s ",
                                               start_time, end_time)
                        self.write_ret(ErrorCode.SUCCESS, 
                                       dict_=DotDict(log_list=allLog))
                except Exception as e:
                    #TODO: 
                    logging.exception("[LOG] Log's inquiry failed. Inquiry condition:"
                                      "start_time: %s"
                                      "end_time: %s"
                                      "plan_id: %s"
                                      "level: %s"
                                      "Exception: %s",
                                      start_time, end_time, plan_id, level, e.args)
                    self.write_ret(ErrorCode.FAILED)
            else:
                # TODO: remove unwanted return
                self.render("log/log.html",
                            allLog={},
                            start_time="",
                            end_time="",
                            plan_id="",
                            level="",
                            username=None,)
