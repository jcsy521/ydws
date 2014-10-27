# -*- coding: utf-8 -*-

import logging
import time

from tornado.escape import json_decode, json_encode
import tornado.web
from tornado.ioloop import IOLoop

from utils.dotdict import DotDict
from codes.errorcode import ErrorCode
from constants import UWEB
from utils.misc import get_acc_status_info_key

from base import BaseHandler, authenticated
from mixin.base import BaseMixin


class ACCHandler(BaseHandler, BaseMixin):

    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            tids = data.get('tids')
            op_type = data.get('op_type')
            logging.info("[UWEB] ACC request: %s, uid: %s, tid: %s, tids: %s", 
                         data, self.current_user.uid, self.current_user.tid, tids)
        except Exception as e:
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return 

        try:
            res = [] 
            for tid in tids:
                r = DotDict(tid=tid,
                            status=ErrorCode.SUCCESS,
                            message=ErrorCode.ERROR_MESSAGE[status])
                try:
                    t = self.db.get("SELECT dev_type FROM T_TERMINAL_INFO"
                                    "  where tid = %s LIMIT 1",
                                    tid)
                    if str(t['dev_type']) != 'D':
                        r['status'] = ErrorCode.ACC_NOT_ALLOWED
                        logging.info("[UWEB] Acc is not allowed. uid: %s, tid: %s, dev_type: %s", 
                                     self.current_user.uid, tid, t['dev_type'])

                    else: 
                        acc_status_info_key = get_acc_status_info_key(tid) 
                        acc_status_info = self.redis.getvalue(acc_status_info_key) 
                        if acc_status_info:
                            r['status'] = ErrorCode.ACC_TOO_FREQUENCY
                            logging.info("[UWEB] Acc is too frequency. uid: %s, tid: %s", 
                                         self.current_user.uid, tid)
                        else:
                            acc_status_info = dict(client_id=self.client_id, 
                                                   op_type=op_type, 
                                                   timestamp=int(time.time()), 
                                                   op_status=0, # failed
                                                   t2_status=0, # wait for T2 
                                                   acc_message=u'') 
                            self.redis.setvalue(acc_status_info_key, acc_status_info, UWEB.ACC_STATUS_EXPIRY)
                except Exception as e: 
                    r['status'] = ErrorCode.FAILED
                    logging.info("[UWEB] Set acc status failed, uid:%s, tid:%s, op_type:%s.", 
                                 self.current_user.uid, tid, op_type)
                finally:
                    r['message'] = ErrorCode.ERROR_MESSAGE[r['status']]
                    res.append(r)
            self.write_ret(status, dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] Set acc status failed, uid:%s, Exception: %s.", 
                              self.current_user.uid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
