# -*- coding: utf-8 -*-

import logging
import time

from tornado.escape import json_decode, json_encode
import tornado.web
from tornado.ioloop import IOLoop
from hashlib import md5

from utils.misc import (get_terminal_info_key, str_to_list, 
     get_terminal_sessionID_key)
from utils.public import update_mannual_status
from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB 

from base import BaseHandler, authenticated
from mixin.base import BaseMixin


class DefendHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        try:
            tid = self.get_argument('tid',None) 
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            
            terminal = self.db.get("SELECT fob_status, mannual_status, defend_status"
                                   "  FROM T_TERMINAL_INFO"
                                   "  WHERE tid = %s"
                                   "    AND (service_status = %s"
                                   "      OR service_status = %s)",
                                   self.current_user.tid,
                                   UWEB.SERVICE_STATUS.ON,
                                   UWEB.SERVICE_STATUS.TO_BE_ACTIVATED)
            if not terminal:
                status = ErrorCode.LOGIN_AGAIN
                logging.error("The terminal with tid: %s does not exist, redirect to login.html", self.current_user.tid)
                self.write_ret(status)
                return
            else:
                terminal_info_key = get_terminal_info_key(self.current_user.tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                mannual_status = terminal_info['mannual_status']

            self.write_ret(status,
                           dict_=DotDict(defend_status=mannual_status, 
                                         mannual_status=mannual_status,
                                         fob_status=terminal.fob_status))
        except Exception as e:
            logging.exception("[UWEB] uid:%s tid:%s get defend status failed. Exception: %s", 
                              self.current_user.uid, self.current_user.tid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
            return 

    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tid = data.get('tid', None) 
            tids = data.get('tids', None)
            # check tid whether exist in request and update current_user
            self.check_tid(tid)
            logging.info("[UWEB] defend request: %s, uid: %s, tid: %s, tids: %s", 
                         data, self.current_user.uid, self.current_user.tid, tids)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            #status = self.check_privilege(self.current_user.uid, self.current_user.tid) 
            #if status != ErrorCode.SUCCESS: 
            #    logging.error("[UWEB] Terminal: %s, user: %s is just for test, has no right to access the function.", 
            #                  tid, self.current_user.uid) 
            #    self.write_ret(status) 
            #    return

            res = [] 
            tids = str_to_list(tids)
            tids = tids if tids else [self.current_user.tid, ]
            tids = [str(tid) for tid in tids]
            for tid in tids:
                r = DotDict(tid=tid,
                            status=ErrorCode.SUCCESS)
                try:
                    terminal = self.db.get("SELECT id FROM T_TERMINAL_INFO"
                                           "  WHERE tid = %s"
                                           "    AND service_status = %s",
                                           tid, UWEB.SERVICE_STATUS.ON)
                    if not terminal:
                        r.status = ErrorCode.LOGIN_AGAIN
                        res.append(r)
                        logging.error("The terminal with tid: %s does not exist, redirect to login.html", tid)
                        continue

                    update_mannual_status(self.db, self.redis, tid, data.mannual_status)

                    logging.info("[UWEB] uid:%s, tid:%s set mannual status to %s successfully", 
                                 self.current_user.uid, tid, data.mannual_status)
                except Exception as e: 
                    r.status = ErrorCode.FAILED
                    logging.error("[UWEB] uid:%s, tid:%s set mannual status to %s failed. Exception: %s", 
                                  self.current_user.uid, tid,
                                  data.mannual_status, e.args)
                finally:
                    res.append(r)

            self.write_ret(status, dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] uid:%s, tid:%s set mannual status to %s failed. Exception: %s", 
                              self.current_user.uid, self.current_user.tid, data.mannual_status, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)

class DefendWeixinHandler(BaseHandler, BaseMixin):

    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            t = self.get_argument('t', None)
            key = self.get_argument('key', None)
            tid = self.get_argument('uid', None)
            mannual_status = self.get_argument('mannual_status', None)
            logging.info("[UWEB] Defend request t:%s, key:%s, tid:%s, mannual_status: %s",
                         t, key, tid, mannual_status)

        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            m = md5()
            pri_key='f36f7c203ea2c7b6f587e223132d9b85'
            m.update(uid+t+pri_key)
            hash_ = m.hexdigest()
            if hash_ != key:
                logging.info("[UWEB] Delegation requeset key wrong")
                raise tornado.web.HTTPError(401)

            update_mannual_status(self.db, self.redis, tid, data.mannual_status)
            self.write_ret(status,)
        except Exception as e:
            logging.exception("[UWEB] tid:%s set mannual status to %s failed. Exception: %s", 
                              tid, data.mannual_status, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
