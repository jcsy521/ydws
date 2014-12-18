# -*- coding: utf-8 -*-

"""This module is designed for captcha.
"""

import tornado.web

import cStringIO
import hashlib

from base import BaseHandler
from mixin.captcha import CaptchaMixin


class CaptchaHandler(BaseHandler, CaptchaMixin):

    """Generate captcha for login.

    :url /captcha
    """

    @tornado.web.removeslash
    def get(self):

        self.generate_captcha('captchahash')


class CaptchaSmsHandler(BaseHandler, CaptchaMixin):

    """Generate captcha for downloading-sms.

    :url /captchasms
    """

    @tornado.web.removeslash
    def get(self):

        self.generate_captcha('captchahash_sms')


class CaptchaImageHandler(BaseHandler, CaptchaMixin):

    """Generate captcha for register.

    :url /captchaimage
    """
    @tornado.web.removeslash
    def get(self):

        self.generate_captcha('captchahash_image')


class CaptchaPasswordHandler(BaseHandler, CaptchaMixin):

    """Generate captcha for password.

    :url /captchapsd
    """
    @tornado.web.removeslash
    def get(self):
        self.generate_captcha('captchahash_password')
