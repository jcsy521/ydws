#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import urllib
import logging
import re

class HttpClient(object):
    
    def send_http_post_request(self, url = None, data = None, encoding = 'utf-8'):
        """
        Send the packet to sms service and receive the response.
        """
        try: 
            # 定义请求对象  
            request = urllib2.Request(url)  
    #        uid=2590&msg=%E4%BD%A0%E5%A5%BD+%E5%88%98%E6%97%B6%E5%98%89%EF%BC%81&msgid=53970002&cmd=send&psw=CEE712A91DD4D0A8A67CC8E47B645662&mobiles=15010955397
            request.add_data(urllib.urlencode(data))
            request.add_header("Content-type", "application/x-www-form-urlencoded")
            # 打开页面获得响应对象
            tries = 3
            while tries:  
                try:  
                    response = urllib2.urlopen(request)  
                    break  
                except Exception, msg:  
                    tries = tries - 1  
                    if tries:  
                        continue  
                    else:  
                        logging.exception("Connection sms service exception : %s", msg)
        
            # 获得响应消息头  
            headerObject = response.headers  
            # 获取响应正文  
            streamData = "" 
            while True:  
                subData = response.read(2048)  
                if subData == "":  
                    break  
                streamData = streamData + subData  
        
            # 判断返回页面的编码机制  
            if headerObject.has_key('Content-Encoding'):  
                if cmp(headerObject['Content-Encoding'].strip().upper(), 'gzip'.upper()) == 0:  
                    compresseddata = streamData  
                    compressedstream = StringIO.StringIO(compresseddata)  
                    gzipper = gzip.GzipFile(fileobj=compressedstream)  
                    htmlCode = gzipper.read()
                else:  
                    htmlCode = streamData  
            else:  
                # 获取返回页面内容  
                htmlCode = streamData  
#            print dir(headerObject)
#            print dict(headerObject)
#            print dir(response)
#            print response.__dict__
            # 判断返回页面内容的编码，并将其转化为utf-8编码  
            if headerObject.has_key('content-type'):  
                contentType = headerObject['content-type']
                # 如果有'charset='这个字符串
                if contentType.lower().find('charset=') != -1:  
                    charset = re.search(r'charset=([^;]*)', contentType.lower()).group(1)
                    if charset != encoding:  
                        try:  
                            htmlCode = htmlCode.decode(charset)
                        except:
                            logging.exception("Encoding return message exception : %s", msg)
            
        except Exception, msg:  
            logging.exception("Send http post request exception : %s", msg)
        finally:
            if response:
                response.close()
                
            return htmlCode




if __name__ == "__main__":
    data = dict(cmd="send",
                uid="2590",
                psw="CEE712A91DD4D0A8A67CC8E47B645662",
                mobiles="18611357615",
                msgid="76150006",
                msg=u"你好 刘时嘉！".encode('gbk')
                )
    htmlCode = send_http_post_request(data)
    print htmlCode
