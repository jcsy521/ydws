# -*- coding:utf-8 -*-

import time 

from utils.misc import (get_terminal_info_key, get_lq_sms_key,
     get_location_key, get_gps_location_key, get_login_time_key,
     get_activation_code, get_acc_status_info_key)
from utils.dotdict import DotDict
from constants import GATEWAY, EVENTER, UWEB

class DMLHelper(object):
    """A bunch of samll functions to modify attributes in the db.

    Compared with QueryHelper(DQL), DMLHelper(DML) is mostly deal with inset, update,
    delete.
    """
    
    @staticmethod
    def modify_acc_status(client_id, tid, op_type, db, redis):
        """Modify the acc_status according to tid.
        """
        acc_status_info_key = get_acc_status_info_key(tid)
        acc_status_info = dict(client_id=client_id,
                               op_type=op_type,
                               timestamp=int(time.time()),
                               op_status=0,
                               is_sent=0, 
                               acc_message=u'')

        redis.setvalue(acc_status_info_key, acc_status_info)
