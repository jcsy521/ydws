# -*- coding: utf-8 -*-

import sys

import os.path
import site
TOP_DIR_ = os.path.abspath(os.path.join(__file__, "../.."))
site.addsitedir(os.path.join(TOP_DIR_, "libs"))
import logging
import re

from tornado.options import define, options, parse_command_line

from helpers.confhelper import ConfHelper
from helpers.smshelper import SMSHelper
from db_.mysql import DBConnection
from utils.myredis import MyRedis
from utils.misc import get_terminal_info_key, get_lastinfo_key, get_location_key

def check_zs_phone(phone, db):
    """Check if the phone is valid.

    @return True: it's safe;
            False: unsafe
    """

    _zs_phone_pattern = r"^(1477847\d{4}|1477874\d{4})$"

    ZS_PHONE_CHECKER = re.compile(_zs_phone_pattern)
    if ZS_PHONE_CHECKER.match(phone):
        return True
    else:
        white_list = db.get("SELECT id FROM T_BIZ_WHITELIST where mobile = %s LIMIT 1", phone)
        if white_list:
            return True
        else:
            return False
def main():
    ConfHelper.load('../conf/global.conf')
    parse_command_line()
    db = DBConnection().db
    redis = MyRedis()
    print check_zs_phone('14715945470', db)

main()
