# -*- coding: utf-8 -*-

import re


_sql_injection_pattern ='|'.join((r"\b(select|update|insert|delete|drop|create|alter|truncate|rename)\b",
                                  r"\b(execute|prepare|call|start|lock|change|use)\b",
                                  r"\b(where|from|join|like)\b",
                                  r"--|#",
                                  r";|&|\\|\*|\^|\(|\)|\%|\$|\>|\<"))

SQL_INJECTION_CHECKER = re.compile(_sql_injection_pattern, re.I)

_phone_pattern = r"^(1\d{10}|0\d{8,11})$"

PHONE_CHECKER = re.compile(_phone_pattern)

_zs_phone_pattern = r"^(1477847\d{4}|1477874\d{4})$"

ZS_PHONE_CHECKER = re.compile(_zs_phone_pattern)

def check_sql_injection(str_):
    """Check if the content has been injected by illegal SQL.

    @return True: it's safe;
            False: unsafe
    """

    return not SQL_INJECTION_CHECKER.search(str_)


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
        white_list = db.get("SELECT id FROM T_BIZ_WHITELIST where mobile = %s LIMIT 1", phone)
        if white_list:
            return True
        else:
            return False
