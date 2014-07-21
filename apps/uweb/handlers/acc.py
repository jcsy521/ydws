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
                            status=ErrorCode.SUCCESS)
                try:
                    acc_status_info_key = get_acc_status_info_key(tid) 
                    acc_status_info = dict(client_id=self.client_id, 
                                           op_type=op_type, 
                                           timestamp=int(time.time()), 
                                           op_status=0, # failed
                                           acc_message=u'') 
                    self.redis.setvalue(acc_status_info_key, acc_status_info, EVENTER.ACC_STATUS_EXPIRY)
                except Exception as e: 
                    r.status = ErrorCode.FAILED
                    logging.info("[UWEB] Set acc status failed, uid:%s, tid:%s, op_type:%s.", 
                                 self.current_user.uid, tid, op_type)
                finally:
                    res.append(r)
            self.write_ret(status, dict_=DotDict(res=res))
        except Exception as e:
            logging.exception("[UWEB] Set acc status failed, uid:%s, Exception: %s.", 
                              self.current_user.uid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
