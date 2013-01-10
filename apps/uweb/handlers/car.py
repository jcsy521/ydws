# -*- coding: utf-8 -*-

import logging
import time

import tornado.web
from tornado.escape import json_encode, json_decode
from tornado.ioloop import IOLoop

from utils.dotdict import DotDict
from utils.misc import get_terminal_info_key
from codes.errorcode import ErrorCode
from constants import SMS
from helpers.seqgenerator import SeqGenerator
from helpers.gfsenderhelper import GFSenderHelper

from mixin.base import  BaseMixin
from base import BaseHandler, authenticated
       
class SwitchCarHandler(BaseHandler, BaseMixin):
    """Switch current car for the current user.
    """
    @authenticated
    @tornado.web.removeslash
    def get(self, tid):
        status = ErrorCode.SUCCESS
        logging.info("[UWEB] switch car request: %s", tid)
        try:
            terminal = self.db.get("SELECT ti.tid, ti.mobile as sim,"
                                  "  ti.login, ti.defend_status "
                                  "  FROM T_TERMINAL_INFO as ti "
                                  "  WHERE ti.tid = %s"
                                  "  LIMIT 1",
                                  tid)
            if terminal: 
                self.send_lq_sms(terminal.sim, tid, SMS.LQ.WEB)
                self.bookkeep(dict(cid=self.current_user.cid,
                                   uid=self.current_user.uid,
                                   tid=tid,
                                   sim=terminal.sim))
                def _on_finish(response):
                    response = json_decode(response)
                    if response['success'] == ErrorCode.SUCCESS:
                        new_fobs = response['params']['FOBS']
                        if new_fobs:
                            fobs = self.db.query("SELECT fobid FROM T_FOB"
                                                 "  WHERE tid = %s",
                                                 tid)
                            old_fobids = [fob.fobid for fob in fobs]
                            new_fobids = new_fobs.split(':')
                            add_fobids = list(set(new_fobids) - set(old_fobids))
                            del_fobids = list(set(old_fobids) - set(new_fobids))
                            for fobid in add_fobids:
                                self.db.execute("INSERT INTO T_FOB(tid, fobid)"
                                                "  VALUES(%s, %s)",
                                                tid, fobid)
                            for fobid in del_fobids:
                                self.db.execute("DELETE FROM T_FOB"
                                                "  WHERE tid = %s"
                                                "    AND fobid = %s",
                                                tid, fobid)
                            if len(old_fobids) != len(new_fobids):
                                self.db.execute("UPDATE T_TERMINAL_INFO"
                                                "  SET keys_num = %s"
                                                "  WHERE tid = %s",
                                                len(new_fobids),
                                                tid)
                            # redis
                            terminal_info_key = get_terminal_info_key(tid)
                            terminal_info = self.redis.getvalue(terminal_info_key)
                            if terminal_info:
                                terminal_info['fob_list'] = new_fobids
                                terminal_info['keys_num'] = len(new_fobids)
                                self.redis.setvalue(terminal_info_key, terminal_info)
                # send S5 for querying fobs 3 minutes later
                seq = str(int(time.time()*1000))[-4:]
                args = DotDict(seq=seq,
                               tid=tid,
                               params=['fobs',])
                IOLoop.instance().add_timeout(int(time.time()) + 180,
                                              lambda: GFSenderHelper.async_forward(
                                                          GFSenderHelper.URLS.QUERY,
                                                          args,
                                                          _on_finish))
            else:
                status = ErrorCode.LOGIN_AGAIN
            self.write_ret(status) 
        except Exception as e:
            logging.exception("[UWEB] uid: %s switch car to tid: %s failed. Exception: %s", 
                              self.current_user.uid, tid, e.args) 
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
