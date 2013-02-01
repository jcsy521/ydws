# -*- coding: utf-8 -*-

def safe_utf8(s):
    if isinstance(s, unicode):
        return s.encode("utf-8", 'ignore')
    assert isinstance(s, str)
    return s
