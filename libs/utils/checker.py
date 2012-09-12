# -*- coding: utf-8 -*-

import re


_sql_injection_pattern ='|'.join((r"\b(select|update|insert|delete|drop|create|alter|truncate|rename)\b",
                                  r"\b(execute|prepare|call|start|lock|change|use)\b",
                                  r"\b(where|from|join|and|or|not|like)\b",
                                  r"--|#",
                                  r";|&|\\|\'|\"|\*|\s|\?|\^|\(|\)|\%|\_|\$"))

SQL_INJECTION_CHECKER = re.compile(_sql_injection_pattern, re.I)

_phone_pattern = r"^(1\d{10}|0\d{8,11})$"

PHONE_CHECKER = re.compile(_phone_pattern)


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

