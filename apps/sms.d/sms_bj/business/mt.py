#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urllib import urlencode
import urllib2
import os.path
import site
import logging
import time
from exceptions import UnicodeEncodeError
from tornado.escape import json_encode, json_decode
import hashlib
import httplib2


import sys
reload(sys)
sys.setdefaultencoding("utf-8")

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
from utils.misc import safe_utf8, safe_unicode

from net.httpclient import HttpClient


class MT(object):
    
    def __init__(self):
        ConfHelper.load(options.conf)
        self.db = DBConnection().db
    
    def fetch_mt_sms(self):
        status = ErrorCode.SUCCESS
        result = None
        try:
            mts = self.db.query("SELECT id, msgid, mobile, content, nosign"
                                "  FROM T_SMS"
                                "  WHERE category = %s"
                                "  AND send_status = %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 50",
                                SMS.CATEGORY.MT, SMS.SENDSTATUS.PREPARING)

            for mt in mts:
                mobile = mt["mobile"]
                content = mt["content"]
                msgid = mt["msgid"]
                id = mt["id"]
                if not mobile:
                    logging.error("[SMS] Mobile is missing, drop it. mt: %s", mt)
                    continue
                if mt["nosign"]:
                    send_status, result = self.send_mt_nosign(id, msgid, mobile, content)  

                    result = eval(result)
                    if send_status["status"] == '200':
                        if result["flag"] == "success":
                            logging.info("SMS-->Gateway nosign message send successfully, mobile:%s, content:%s",
                                         mobile, content)
                            status = ErrorCode.SUCCESS
                            self.db.execute("UPDATE T_SMS "
                                           "  SET send_status = %s"
                                           "  WHERE id = %s",
                                           SMS.SENDSTATUS.SUCCESS, id)
                        else:
                            logging.error("SMS-->Gateway nosign message send failed, result:%s",
                                          result)
                            status = ErrorCode.FAILED
                            self.db.execute("UPDATE T_SMS "
                                                "  SET send_status = %s"
                                                "  WHERE id = %s",
                                                SMS.SENDSTATUS.FAILURE, id)
                    else:
                        logging.error("SMS-->Gateway nosign message failed, send_status:%s",
                                      send_status)
                        status = ErrorCode.FAILED
                        self.db.execute("UPDATE T_SMS "
                                        "  SET send_status = %s"
                                        "  WHERE id = %s",
                                        SMS.SENDSTATUS.FAILURE, id)
                    
                else:
                    result = self.send_mt(id, msgid, mobile, content)
                    result = json_decode(result)
                    
                    if result["status"] == ErrorCode.SUCCESS:
                        if result["ret"] == "100":
                            logging.info("SMS-->Gateway success mobile = %s, content = %s, id = %s ", mobile, content, id)
                            self.db.execute("UPDATE T_SMS "
                                           "  SET send_status = %s"
                                           "  WHERE id = %s",
                                           SMS.SENDSTATUS.SUCCESS, id)
                            status = ErrorCode.SUCCESS
                        else:
                            if result["ret"] == "101":
                                logging.error("SMS-->Gateway failure, errorcode = 101, mobile = %s, content = %s, id = %s ", mobile, content, id)
                            elif result["ret"] == "104":
                                logging.error("SMS-->Gateway content error, errorcode = 104, mobile = %s, content = %s, id = %s ", mobile, content, id)
                            elif result["ret"] == "105":
                                logging.error("SMS-->Gateway frequency too fast, errorcode = 105, mobile = %s, content = %s, id = %s ", mobile, content, id)
                            elif result["ret"] == "106":
                                logging.error("SMS-->Gateway number limited, errorcode = 106, mobile = %s, content = %s, id = %s ", mobile, content, id)
                            else:
                                logging.error("SMS-->Gateway other error, errorcode unknown, mobile = %s, content = %s, id = %s ", mobile, content, id)
                                
                            if  result["ret"] != "105":
                                self.db.execute("UPDATE T_SMS "
                                                "  SET send_status = %s"
                                                "  WHERE id = %s",
                                                SMS.SENDSTATUS.FAILURE, id)
                            status = ErrorCode.FAILED
                    else:
                        # http response is None
                        logging.info("SMS-->Gateway failed, mobile = %s, content = %s, id = %s ", mobile, content, id)
                        status = ErrorCode.FAILED
                        self.db.execute("UPDATE T_SMS "
                                        "  SET send_status = %s"
                                        "  WHERE id = %s",
                                        SMS.SENDSTATUS.FAILURE, id)
            
        except Exception, msg:
            status = ErrorCode.FAILED
            logging.exception("Fetch mt sms exception : %s", msg)
        finally:
            return status
    
    
    def send_mt(self, id, msgid, mobile, content):
        response = {'status': ErrorCode.FAILED, 'ret' : '100'}
        try:
            url = ConfHelper.SMS_CONF.mt_url
            msgid = msgid
            mobiles = mobile
            msg = content
            req = urllib2.Request(url=url,
                                  data=urlencode(dict(mobiles=mobiles,
                                                      msg=msg,
                                                      msgid=msgid)))
            f = urllib2.urlopen(req)
            response = f.read()
           
        except UnicodeEncodeError, msg:
            self.db.execute("UPDATE T_SMS "
                            "  SET send_status = %s, "
                            "  recv_status = %s, "
                            "  retry_status = %s "
                            "  WHERE id = %s",
                            SMS.SENDSTATUS.FAILURE, SMS.USERSTATUS.FAILURE, 
                            SMS.RETRYSTATUS.YES, id)
            logging.exception("MT sms encode exception : %s, msgid:%s, id:%s", msg, msgid, id)
        except Exception, msg:
            logging.exception("Send mt sms exception : %s, msgid:%s, id:%s", msg, msgid, id)
        finally:
            f.close()
            return response
        
    #NOTE: old version
    #def send_mt(self, id, msgid, mobile, content):
    #    result = {'status': ErrorCode.FAILED, 'ret' : '100'}
    #    try:
    #        url = ConfHelper.SMS_CONF.mt_url
    #        cmd = "send"
    #        uid = ConfHelper.SMS_CONF.uid
    #        psw = ConfHelper.SMS_CONF.psw
    #        msgid = msgid
    #        mobiles = mobile
    #        msg = content.encode('gbk')

    #        data = dict(cmd=cmd,
    #                    uid=uid,
    #                    psw=psw,
    #                    mobiles=mobiles,
    #                    msgid=msgid,
    #                    msg=msg
    #                    )            

    #        result = HttpClient().send_http_post_request(url, data)
    #        
    #    except UnicodeEncodeError, msg:
    #        self.db.execute("UPDATE T_SMS "
    #                        "  SET send_status = %s, "
    #                        "  recv_status = %s, "
    #                        "  retry_status = %s "
    #                        "  WHERE id = %s",
    #                        SMS.SENDSTATUS.FAILURE, SMS.USERSTATUS.FAILURE, 
    #                        SMS.RETRYSTATUS.YES, id)
    #        logging.exception("MT sms encode exception : %s, msgid:%s, id:%s", msg, msgid, id)
    #    except Exception, msg:
    #        logging.exception("Send mt sms exception : %s, msgid:%s, id:%s", msg, msgid, id)
    #    finally:
    #        return result
    
    def fetch_failed_mt_sms(self):
        status = ErrorCode.SUCCESS
        result = {'status': ErrorCode.FAILED, 'ret' : '100'}
        try:
            mts = self.db.query("SELECT id, msgid, mobile, content, insert_time "
                                "  FROM T_SMS "
                                "  WHERE category = %s "
                                "  AND send_status = %s"
                                "  OR recv_status != %s"
                                "  AND retry_status = %s"
                                "  ORDER BY id ASC"
                                "  LIMIT 10",
                                SMS.CATEGORY.MT, SMS.SENDSTATUS.FAILURE, 
                                SMS.USERSTATUS.SUCCESS, SMS.RETRYSTATUS.NO)
            for mt in mts:
                mobile = mt["mobile"]
                content = mt["content"]
                msgid = mt["msgid"]
                id = mt["id"]
                insert_time = mt["insert_time"]
                
                current_time = int(time.time() * 1000)
                ONE_MIN = 60 * 1000 # millisecond
                
                if current_time - int(insert_time) > ONE_MIN:
                    result = self.send_mt(id, msgid, mobile, content)
                    
                    if result["status"] == ErrorCode.SUCCESS:
                        if result["ret"] == "100":
                            logging.info("SMS-->Gateway retry success mobile = %s, content = %s, id = %s ", mobile, content, id)
                            self.db.execute("UPDATE T_SMS "
                                           "  SET send_status = %s"
                                           "  WHERE id = %s",
                                           SMS.SENDSTATUS.SUCCESS, id)
                            status = ErrorCode.SUCCESS
                        else:
                            if result["ret"] == "101":
                                logging.error("SMS-->Gateway retry failure, errorcode = 101, mobile = %s, content = %s, id = %s ", mobile, content, id)
                            elif result["ret"] == "104":
                                logging.error("SMS-->Gateway retry content error, errorcode = 104, mobile = %s, content = %s, id = %s ", mobile, content, id)
                            elif result["ret"] == "105":
                                logging.error("SMS-->Gateway retry frequency too fast, errorcode = 105, mobile = %s, content = %s, id = %s ", mobile, content, id)
                            elif result["ret"] == "106":
                                logging.error("SMS-->Gateway retry number limited, errorcode = 106, mobile = %s, content = %s, id = %s ", mobile, content, id)
                            else:
                                logging.error("SMS-->Gateway retry other error, errorcode unknown, mobile = %s, content = %s, id = %s ", mobile, content, id)
                                
                            if  result["ret"] != "105":
                                self.db.execute("UPDATE T_SMS "
                                                "  SET send_status = %s"
                                                "  WHERE id = %s",
                                                SMS.SENDSTATUS.FAILURE, id)
                            status = ErrorCode.FAILED
                    else:
                        # http response is None
                        status = ErrorCode.FAILED
                        self.db.execute("UPDATE T_SMS "
                                        "  SET send_status = %s"
                                        "  WHERE id = %s",
                                        SMS.SENDSTATUS.FAILURE, id)
                    self.db.execute("UPDATE T_SMS "
                                    "  SET retry_status = %s"
                                    "  WHERE id = %s",
                                    SMS.RETRYSTATUS.YES, id)
                else:
                    pass
        except Exception, msg:
            status = ErrorCode.FAILED
            logging.exception("Fetch failed mt sms exception : %s", msg)
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

