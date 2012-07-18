# -*- coding: utf-8 -*-

import tornado.web

import Image, ImageDraw, ImageFont, ImageFilter 
import random
import string
import cStringIO
import hashlib
import datetime
import os.path

from utils.dotdict import DotDict

from base import BaseHandler


class CaptchaHandler(BaseHandler):

    FONT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "monaco.ttf")

    @tornado.web.removeslash
    def get(self):

        size = (123, 25)
        jam_num = (1, 2)
        point_border = (100, 97)
        
        im = Image.new('RGB', size, (255, 255, 255))
        draw = ImageDraw.Draw(im)

        rand_str = ''.join(random.choice(string.letters + string.digits) for x in range(4))
        
        draw.text((random.randint(1, 5), -2),
                  rand_str[0],
                  fill=(0, 0, 255),
                  font=ImageFont.truetype(self.FONT_FILE, random.randint(18, 20)))
        draw.text((random.randint(30, 40), -2),
                  rand_str[1],
                  fill=(255, 0, 0),
                  font=ImageFont.truetype(self.FONT_FILE, random.randint(18, 20)))
        draw.text((random.randint(55, 65), -2),
                  rand_str[2], 
                  fill=(0, 0, 255),
                  font=ImageFont.truetype(self.FONT_FILE, random.randint(18, 20)))
        draw.text((random.randint(80, 90), -2),
                  rand_str[3],
                  fill=(255, 0, 0),
                  font=ImageFont.truetype(self.FONT_FILE, random.randint(18, 20)))
        
        # noise lines
        line_num = random.randint(jam_num[0], jam_num[1])
        for i in range(line_num):
            begin = (random.randint(0, size[0]), random.randint(0, size[1]))
            end = (random.randint(0, size[0]), random.randint(0, size[1])) 
            draw.line([begin, end], fill=(0, 0, 0))

        # noise points
        for x in range(size[0]):
            for y in range(size[1]):
                flag = random.randint(0, point_border[0])
                if flag > point_border[1]:
                    draw.point((x, y), fill=(0, 0, 0))
                    #del flag

        # # twist the figure 
        # para = [1 - float(random.randint(1, 2))/100, 
        #         0, 
        #         0, 
        #         0, 
        #         1 - float(random.randint(1, 10))/100, 
        #         float(random.randint(1, 2))/500, 
        #         0.001,
        #         float(random.randint(1, 2))/500]
        # im = im.transform(im.size, Image.PERSPECTIVE,para)
        # im = im.filter(ImageFilter.EDGE_ENHANCE_MORE)

        buf = cStringIO.StringIO()
        im.save(buf, 'gif')

        m = hashlib.md5()
        m.update(rand_str.lower()) 
        hash_ = m.hexdigest()

        self.set_cookie('captchahash', hash_)
        self.set_header('Content-type', 'image/GIF')
        self.write(buf.getvalue())
