# -*- coding: utf-8 -*-

import logging

from constants import UWEB
from codes.smscode import SMSCode
from utils.misc import (get_terminal_info_key, 
    safe_utf8, get_alert_freq_key)
from utils.public import (clear_sessionID, 
    get_use_scene_by_vibl, add_user, update_mannual_status)

from helpers.queryhelper import QueryHelper
from helpers.wspushhelper import WSPushHelper
from helpers.smshelper import SMSHelper

from base import BaseMixin


class TerminalMixin(BaseMixin):

    """Mix-in for terminal related functions."""

    def update_terminal_db(self, data):
        """Update database.
        """
        # NOTE: these fields should to be modified in db
        terminal_keys = ['cellid_status', 'white_pop', 'trace', 'freq',
                         'vibchk', 'vibl', 'push_status', 'login_permit',
                         'alert_freq', 'stop_interval', 'biz_type', 'speed_limit']
        terminal_fields = []

        if data.has_key('tid'):
            del data['tid']

        for key, value in data.iteritems():

            # NOTE: These fields should be modified in database.
            if key in terminal_keys:
                if data.get(key, None) is not None:
                    terminal_fields.append(key + ' = ' + str(value))
                    
            # NOT: These fields should be handled specially.
            if key == 'white_list':
                white_list = data[key]
                if len(data['white_list']) < 1:
                    pass
                else:
                    self.db.execute("DELETE FROM T_WHITELIST WHERE tid = %s",
                                    self.current_user.tid)
                    for white in white_list[1:]:
                        self.db.execute("INSERT INTO T_WHITELIST"
                                        "  VALUES(NULL, %s, %s)"
                                        "  ON DUPLICATE KEY"
                                        "  UPDATE tid = VALUES(tid),"
                                        "    mobile = VALUES(mobile)",
                                        self.current_user.tid, white)

            elif key == 'alias':
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET alias = %s"
                                "  WHERE tid = %s",
                                value, self.current_user.tid)

                terminal_info_key = get_terminal_info_key(
                    self.current_user.tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                if terminal_info:
                    terminal_info[key] = value
                    self.redis.setvalue(terminal_info_key, terminal_info)
            elif key == 'icon_type':
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET icon_type = %s"
                                "  WHERE tid = %s",
                                value, self.current_user.tid)

                terminal_info_key = get_terminal_info_key(
                    self.current_user.tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                if terminal_info:
                    terminal_info[key] = value
                    self.redis.setvalue(terminal_info_key, terminal_info)
            elif key == 'corp_cnum':
                self.db.execute("UPDATE T_CAR"
                                "  SET cnum = %s"
                                "  WHERE tid = %s",
                                safe_utf8(value), self.current_user.tid)
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET alias = %s"
                                "  WHERE tid = %s",
                                safe_utf8(value), self.current_user.tid)
                terminal_info_key = get_terminal_info_key(
                    self.current_user.tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                if terminal_info:
                    terminal_info[
                        'alias'] = value if value else self.current_user.sim
                    self.redis.setvalue(terminal_info_key, terminal_info)
            elif key == 'owner_mobile' and value is not None:
                umobile = value
                user = dict(umobile=umobile,
                            password=u'111111')
                add_user(user, self.db, self.redis)   
                t = QueryHelper.get_terminal_by_tid(self.current_user.tid, self.db)                
                old_uids = [t.owner_mobile]
                # send sms                
                self.db.execute("UPDATE T_TERMINAL_INFO"
                                "  SET owner_mobile = %s"
                                "  WHERE tid = %s",
                                umobile, self.current_user.tid)
                register_sms = SMSCode.SMS_REGISTER % (
                    umobile, self.current_user.sim)
                SMSHelper.send_to_terminal(self.current_user.sim, register_sms)

                # update redis
                terminal_info_key = get_terminal_info_key(
                    self.current_user.tid)
                terminal_info = self.redis.getvalue(terminal_info_key)
                if terminal_info:
                    terminal_info[key] = umobile
                    self.redis.setvalue(terminal_info_key, terminal_info)

                # wspush to client
                WSPushHelper.pushS3(self.current_user.tid, self.db, self.redis)
                WSPushHelper.pushS3_dummy(old_uids, self.db, self.redis)
            elif key == "alert_freq":
                alert_freq_key = get_alert_freq_key(self.current_user.tid)
                if self.redis.exists(alert_freq_key):
                    logging.info(
                        "[UWEB] Termianl %s delete alert freq in redis.", self.current_user.tid)
                    self.redis.delete(alert_freq_key)

            # if vibl has been changed,then update use_scene as well
            elif key == "vibl":
                use_scene = get_use_scene_by_vibl(value)
                self.db.execute("UPDATE T_TERMINAL_INFO SET use_scene=%s WHERE tid=%s",
                                use_scene, self.current_user.tid)
                logging.info("[UWEB] Terminal %s update use_scene %s and vibl %s",
                             self.current_user.tid, use_scene, value)
                logging.info(
                    "[UWEB] Termianl %s delete session in redis.", self.current_user.tid)
            # NOTE: deprecated.
            elif key == "parking_defend" and value is not None:
                if value == 1:
                    mannual_status = UWEB.DEFEND_STATUS.SMART
                else:
                    mannual_status = UWEB.DEFEND_STATUS.YES
                update_mannual_status(
                    self.db, self.redis, self.current_user.tid, mannual_status)
            elif key == 'login_permit':
                # wspush to client
                WSPushHelper.pushS3(self.current_user.tid, self.db, self.redis)                
            else:
                pass               

        # NOTE:update database.
        terminal_clause = ','.join(terminal_fields)
        if terminal_clause:
            self.db.execute("UPDATE T_TERMINAL_INFO"
                            "  SET " + terminal_clause +
                            "  WHERE tid = %s ",
                            self.current_user.tid)
        # NOTE: clear sessionID if freq, stop_interval, vibl can be found.
        if data.has_key('freq') or data.has_key('stop_interval') or data.has_key('vibl'):
            clear_sessionID(self.redis, self.current_user.tid)
