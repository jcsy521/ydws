#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time

import tornado.web

from basehandler import BaseHandler
from constants import SMS
from codes.errorcode import ErrorCode


class ACBMTHandler(BaseHandler):
    
    @tornado.web.removeslash
    def post(self):
        insert_time = int(time.time() * 1000)
        msgid = str(insert_time)[-9:]
        try:
            content = self.get_argument("content")
            mobile = self.get_argument("mobile")
            nosign = self.get_argumnet("nosign")
            if str(mobile) == '13432119832':
                logging.info("[SMS] special mobile: %s, check huanka", mobile)
                if u'换卡' in content:
                    logging.info("[SMS] mobile: %s, content: %s is in black list, so skip the sms.", mobile, content)
                    self.write({'status' : ErrorCode.SUCCESS, 'msgid' : msgid})
                    return
                
            
            black_list = ('15819954159','13902820929','13450950869','13823921010','13822782382','13652230073','13703047912',
                          '13703047912','13823990298','13726107664','13411656959','15220936365','13702350426','13823922933',
                          '13928184846','15819975339','15220938533','13416058872','13532063411','13590715788','15889888140',
                          '13703041733','15976025624','15017335473','13702533993','18219251647','13528189287','18344911924',
                          # '13432119832'
                          '13822769118',
                          )
            if mobile in black_list:
                logging.info("[SMS] %s is in black list, so skip the sms.", mobile)
                self.write({'status' : ErrorCode.SUCCESS, 'msgid' : msgid})
                return

            cm = int(mobile[:3])
            cm_list = (139,138,137,136,135,134,159,150,151,158,157,188,187,152,182,183,184,147)
            
            if cm not in cm_list:
                logging.info("[SMS] %s is not China Mobile, so skip the sms.", mobile)
                self.write({'status' : ErrorCode.SUCCESS, 'msgid' : msgid})
                return
            
            self.db.execute("INSERT INTO T_SMS(msgid, mobile, content, "
                            " insert_time, category, send_status, nosign) "
                            "  VALUES(%s, %s, %s, %s, %s, %s, %s)",
                            msgid, mobile, content, insert_time,
                            SMS.CATEGORY.MT, SMS.SENDSTATUS.PREPARING, nosign)
            logging.info("[SMS] acb-->sms save success! mobile = %s, content = %s, nosign:%s", mobile, content, nosign)
            self.write({'status' : ErrorCode.SUCCESS, 'msgid' : msgid})
        except Exception, msg:  
            logging.exception("[SMS] acb-->sms post exception : %s", msg)
            self.write({'status' : ErrorCode.FAILED, 'msgid' : msgid})
        
        
