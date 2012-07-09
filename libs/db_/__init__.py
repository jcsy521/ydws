# -*- coding: utf-8 -*-

from helpers.confhelper import ConfHelper

def load_config(conf_file):
    """Load configurations before setting up connections."""

    if not ConfHelper.loaded:
        ConfHelper.load(conf_file)
