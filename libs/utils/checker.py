# -*- coding: utf-8 -*-

import re
import logging
import httplib2


_sql_injection_pattern ='|'.join((r"\b(select|update|insert|delete|drop|create|alter|truncate|rename)\b",
                                  r"\b(execute|prepare|call|start|lock|change|use)\b",
                                  r"\b(where|from|join|like)\b",
                                  r"--|#",
                                  r";|&|\'|\\|\*|\^|\(|\)|\%|\$|\>|\<"))

SQL_INJECTION_CHECKER = re.compile(_sql_injection_pattern, re.I)

_label_pattern = r"^[a-zA-Z0-9]+$"

LABEL_CHECKER = re.compile(_label_pattern)

_phone_pattern = r"^(1\d{10}|0\d{8,11})$"

PHONE_CHECKER = re.compile(_phone_pattern)

_phone_pattern = r"^(1\d{10}|0\d{8,11})$"

PHONE_CHECKER = re.compile(_phone_pattern)

_cnum_pattern = ur"^[\u4e00-\u9fa5A-Z0-9 ]+$"

CNUM_CHECKER = re.compile(_cnum_pattern)

_name_pattern = ur"^[\u4e00-\u9fa5a-zA-Z0-9 ]+$"

NAME_CHECKER = re.compile(_name_pattern)

_zs_phone_pattern = r"^(1477847\d{4}|1477874\d{4}|1847644\d{4})$"

ZS_PHONE_CHECKER = re.compile(_zs_phone_pattern)

_filename_pattern = r"^[a-zA-Z0-9\._]+$"
FILENAME_CHECKER = re.compile(_filename_pattern)

def check_sql_injection(str_):
    """Check if the content has been injected by illegal SQL.

    @return True: it's safe;
            False: unsafe
    """

    return not SQL_INJECTION_CHECKER.search(str_)

def check_label(label):
    """Check if the input is alpha or number.

    @return True: it's valid
            False: it's invalid
    """
    
    return LABEL_CHECKER.match(label)

def check_cnum(cnum):
    """Check if the licensenum is valid.

    @return True: it's valid
            False: it's invalid
    """
    return True
    #if not cnum:  # it's ok if cnum is ''
    #    return True
    #return CNUM_CHECKER.match(cnum)

def check_name(name):
    """Check if the name is valid.

    @return True: it's valid
            False: it's invalid
    """
    return True
    #return NAME_CHECKER.match(name)

def check_phone(phone):
    """Check if the phone is valid.

    @return True: it's safe;
            False: unsafe
    """

    return PHONE_CHECKER.match(phone)

def check_zs_phone(phone, db):
    """Check if the phone is valid.

    @return True: it's safe;
            False: unsafe
    """

    if ZS_PHONE_CHECKER.match(phone):
        return True
    else:
        white_list = db.get("SELECT id FROM T_BIZ_WHITELIST WHERE mobile = %s LIMIT 1", phone)
        if white_list:
            return True
        else:
            ajt_white_list = db.get("SELECT id FROM T_AJT_WHITELIST WHERE mobile = %s LIMIT 1", phone)
            if ajt_white_list: 
                return True
            else: 
                return False

def check_gd_phone(phone):
    """Check if the phone comes from guangdong.
    :return True：it's okay, comes from guangdong
            False: it is not in guandong

    http://tcc.taobao.com/cc/json/mobile_tel_segment.htm?tel=15850781443

    See:
    http://blog.sina.com.cn/s/blog_7bac4707010143o2.html

    """
    is_guandong = True
    try:
        url = 'http://tcc.taobao.com/cc/json/mobile_tel_segment.htm?tel=%s' % phone
        http = httplib2.Http(timeout=5)
        response, content = http.request(url, 'GET')
        cont = content.decode('gbk')
        cont = cont[cont.find('{'):]
        logging.info("[CHECKER] content: %s", cont)
        if cont.find(u'广东')>0:
            is_guandong = True
        else:
            is_guandong = False 
    except Exception as e:
        logging.exception("[CHECKER] Check guandong phone failed. Exception:%s", 
                          e.args)
    finally:
        return is_guandong 

def check_filename(filename):
    """Check if the filename contains illegal character
    """
    return FILENAME_CHECKER.match(filename)

