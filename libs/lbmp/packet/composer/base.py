# -*- coding: utf-8 -*-

class BaseComposer(object):
   
    def __init__(self) :
        
        self.template = ""
      
    def get_request(self):
        
        message = self.template
        return message.encode("gbk")
