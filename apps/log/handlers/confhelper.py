# -*- coding: utf-8 -*-

import ConfigParser
from utils.dotdict import DotDict


class ConfHelper(object):
    """Load sender (and/or sms) configurations from conf file and
    provide them as global variables.
    """
    # prevent for multiple loads
    _HAVE_LOADED = False

    @property
    @classmethod
    def loaded(cls):
        return cls._HAVE_LOADED

    @classmethod
    def load(cls, conf_file):
        """load definitoins from conf_file."""

        if cls._HAVE_LOADED:
            return

        cfg = ConfigParser.ConfigParser()
        cfg.read(conf_file)

        for section in cfg.sections():
            sec_conf = section.upper() + "_CONF"

            setattr(cls, sec_conf, DotDict())
            for k, v in cfg.items(section):
                getattr(cls, sec_conf)[k.lower()] = v

        cls._HAVE_LOADED = True
