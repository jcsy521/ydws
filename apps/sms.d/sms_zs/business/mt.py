#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import site
import logging
import time
from exceptions import UnicodeEncodeError
import hashlib
import httplib2
from urllib import urlencode

TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../../../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
site.addsitedir(os.path.join(TOP_DIR_, "apps/sms"))

from tornado.options import define, options
if 'conf' not in options:
    define('conf', default=os.path.join(TOP_DIR_, "conf/global.conf"))

from helpers.confhelper import ConfHelper
from db_.mysql import DBConnection
from constants import SMS
from codes.errorcode import ErrorCode
from net.httpclient import HttpClient
from util.smscomposer import SMSComposer
from util.smsparser import SMSParser

class MT(object):
    
    def __init__(self, queue):
        ConfHelper.load(options.conf)
        self.db = DBConnection().db
        self.queue = queue 

    def add_sms_to_queue(self):
        status = ErrorCode.SUCCESS
        try:
            mts = self.db.query("SELECT id, msgid, mobile, content,nosign"
                                "  FROM T_SMS "
                                "  WHERE category = %s "
                                "  AND send_status = %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 50",
                                SMS.CATEGORY.MT, SMS.SENDSTATUS.PREPARING)

            for mt in mts:
                mobile = mt["mobile"]
                content = mt["content"]
                msgid = mt["msgid"]
                id = mt["id"]
                nosign = mt["nosign"]
                packet = SMSComposer(mobile, content).result
                url = ConfHelper.SMS_CONF.mt_url
                sms = {"url":url,
                       "packet":packet,
                       "msgid":msgid,
                       "mobile":mobile,
                       "content":content,
                       "id":id,
                       "nosign":nosign}
                self.queue.put(sms)
                self.db.execute("UPDATE T_SMS"
                                "  SET send_status = %s"
                                "  WHERE id = %s",
                                SMS.SENDSTATUS.SENDING, id)
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("[SMS] add sms to queue exception: %s", e.args)
        finally:
            return status

    def send_sms(self, sms):
        try:
            status = ErrorCode.SUCCESS
            if sms["nosign"]:
                send_status, result = self.send_mt_nosign(sms["id"], sms["msgid"], sms["mobile"], sms["content"])

                result = eval(result)
                if send_status["status"] == '200':
                    if result["resultCode"] == "0":
                    #if result["flag"] == "success":
                        logging.info("SMS-->Gateway nosign message send successfully, mobile:%s, content:%s",
                                     sms["mobile"], sms["content"])
                        status = ErrorCode.SUCCESS
                        self.db.execute("UPDATE T_SMS "
                                        "  SET send_status = %s"
                                        "  WHERE id = %s",
                                        SMS.SENDSTATUS.SUCCESS, sms["id"])
                    else:
                        logging.error("SMS-->Gateway nosign message send failed, result:%s",
                                      result)
                        status = ErrorCode.FAILED
                        self.db.execute("UPDATE T_SMS "
                                        "  SET send_status = %s"
                                        "  WHERE id = %s",
                                        SMS.SENDSTATUS.FAILURE, sms["id"])
                else:
                    logging.error("SMS-->Gateway nosign message failed, send_status:%s",
                                  send_status)
                    status = ErrorCode.FAILED
                    self.db.execute("UPDATE T_SMS "
                                    "  SET send_status = %s"
                                    "  WHERE id = %s",
                                    SMS.SENDSTATUS.FAILURE, id) 

            else:
                result = HttpClient().send_http_post_request(sms['url'], sms['packet'])
                if result["status"] == ErrorCode.SUCCESS:
                    parser_result = SMSParser(result["response"])
                    response_code = parser_result.response_code
                    response_text = parser_result.response_text
                    if response_code == "0":
                        logging.info("[SMS] SMS-->Gateway success mobile = %s, content = %s, id= %s ", 
                                     sms['mobile'], sms['content'], sms['id'])
                        self.db.execute("UPDATE T_SMS "
                                       "  SET send_status = %s"
                                       "  WHERE id = %s",
                                       SMS.SENDSTATUS.SUCCESS, sms['id'])
                    else:
                        status = ErrorCode.FAILED
                        if response_code == "5":
                            logging.error("[SMS] SMS-->Gateway failure, gateway fault, errorcode = 5, mobile = %s, content = %s, id = %s ", 
                                          sms['mobile'], sms['content'], sms['id'])
                        else:
                            logging.error("[SMS] SMS-->Gateway other error, errorcode = %s errortext = %s, mobile = %s, content = %s, id = %s ", 
                                          response_code, response_text,
                                          sms['mobile'], sms['content'], sms['id'])
                            
                            self.db.execute("UPDATE T_SMS "
                                            "  SET send_status = %s"
                                            "  WHERE id = %s",
                                            SMS.SENDSTATUS.FAILURE, sms['id'])
                else:
                    status = ErrorCode.FAILED
                    self.db.execute("UPDATE T_SMS "
                                    "  SET send_status = %s"
                                    "  WHERE id = %s",
                                    SMS.SENDSTATUS.FAILURE, sms['id'])
                    logging.error("[SMS] SMS execute send_http_post_request() failure, mobile = %s, content = %s, id = %s ", 
                                  sms['mobile'], sms['content'], sms['id'])
                
        except UnicodeEncodeError as e:
            self.db.execute("UPDATE T_SMS"
                            "  SET send_status = %s, "
                            "  retry_status = %s "
                            "  WHERE id = %s",
                            SMS.SENDSTATUS.FAILURE,
                            SMS.RETRYSTATUS.YES, sms['id'])
            logging.exception("[SMS] Send sms encode exception : %s, msgid:%s, id:%s", 
                              e.args, sms['msgid'], sms['id'])
        except Exception as e:
            status = ErrorCode.FAILED
            logging.exception("[SMS] Send sms exception : %s", e.args)
        finally:
            return status

    def send_mt_nosign(self, id, msgid, mobile, content):
        url = 'http://120.197.89.173:8081/openapi/router'
        secret = '494e58f3a9808daea3bef94078563109'
        # system_para
        appKey = 'j1baerwhjp'
        sessionId = ''
        method = 'sms.service.send'
        v = '1.0'
        format = 'json'
        locale = ''
        sign = ''  #upper()
        system_para_dict = dict(appKey=appKey,
                            method=method,
                            v=v,
                            format=format,
                            locale=locale,
                            sessionId=sessionId,
                            sign=sign)

        system_para_list = []
        business_para_list = []
        system_para_list = ["appKey" + appKey, "method" + method, "v" + v, "format" + format]
        if locale:
            system_para_list.append("locale"+locale)
        if sessionId:
            system_para_list.append("sessionId"+sessionId)

        #business_para
        phoneNumbers = mobile
        Content = content
        EntCode = '106571205329'
        ReportId = msgid
        isImmediately = True  #lower

        business_para_list = ["phoneNumbers"+phoneNumbers, "Content"+Content, "EntCode"+EntCode, "ReportId"+str(ReportId), "isImmediately"+str(isImmediately)]
        business_para_dict = dict(phoneNumbers=phoneNumbers,
                                  Content=Content,
                                  EntCode=EntCode,
                                  ReportId=ReportId,
                                  isImmediately=isImmediately)

        parameters_list = self.get_parameters_list(system_para_list, business_para_list)
        sign = self.get_sign(secret, parameters_list)
        system_para_dict['sign'] = sign
        request_url = self.get_request_url(url, system_para_dict, business_para_dict)

        h = httplib2.Http()
        send_status, result = h.request(request_url)
        return send_status, result

    def get_parameters_list(self, system_para_list, business_para_list):
        parameters_list = []
        parameters_list.extend(system_para_list)
        parameters_list.extend(business_para_list)
        parameters_list.sort()
        return parameters_list

    def get_sign(self, secret, parameters_list):
        parameters_str = ''.join(parameters_list)
        str = secret + parameters_str + secret

        sha1 = hashlib.sha1()
        sha1.update(str)
        mysign = sha1.hexdigest()
        sign = mysign.upper()
        return sign

    def get_request_url(self, url, system_para_dict, business_para_dict):
        request_url_list = []
        request_url = url + "?"
        for k, v in system_para_dict.iteritems():
            if v:
                s = k + "=" + str(v)
                request_url_list.append(s)

        for k, v in business_para_dict.iteritems():
            if v:
                if k == "Content":
                    content_dict = {'Content': v}
                    v = urlencode(content_dict)
                    request_url_list.append(v)
                    continue
                s = k + "=" + str(v)
                request_url_list.append(s)

        request_url_list_str = '&'.join(request_url_list)
        request_url = request_url + request_url_list_str
        return request_url


