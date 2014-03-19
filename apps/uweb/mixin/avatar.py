# -*- coding: utf-8 -*-

import time
import os
import Image

from base import BaseMixin
from utils.misc import get_avatar_time_key
from constants import UWEB

class AvatarMixin(BaseMixin):
    """  Mix-in for avatar information functions.
    """

    def get_avatar_info(self, mobile):
        """get avatar_full_path, avatar_path, avatar_name, avatar_time of avatar.
        @params: mobile 
        @return: avatar_full_path, the full path in server
                 avatar_path, , the relative path for client and browser
                 avatar_name, the name of the avatar. if not avatar, provide default.png
                 avatar_time, the last modified time for avatar. if not avatar, provide 0
        """
        avatar_name = mobile + '.png'
        avatar_path = self.application.settings['avatar_path'] + avatar_name
        avatar_full_path = self.application.settings['server_path'] + avatar_path
        avatar_time = self.get_avatar_time(mobile)
        if not os.path.isfile(avatar_full_path):
            avatar_time = 0
            avatar_name = 'default.png'
            avatar_path = self.application.settings['avatar_path'] + avatar_name
            avatar_full_path = self.application.settings['server_path'] + avatar_path
        return avatar_name, avatar_path, avatar_full_path, avatar_time

    def get_avatar_time(self, mobile):
        """get avatar_time of the avatar.
        """
        avatar_time_key = get_avatar_time_key(mobile)
        avatar_time = self.redis.getvalue(avatar_time_key)
        return avatar_time if avatar_time else 0

    def update_avatar_time(self, mobile):
         """update the avatar_time when avatar is modified.
         """
         avatar_time_key = get_avatar_time_key(mobile)
         avatar_time = int(time.time())
         self.redis.setvalue(avatar_time_key, avatar_time)
         return avatar_time

    def make_thumb(self, path):
        img = Image.open(path)
        thumb = img.resize((UWEB.AVATAR_SIZE.WIDTH, UWEB.AVATAR_SIZE.HEIGHT))
        thumb.save(path, quality = UWEB.AVATAR_QUALITY)
