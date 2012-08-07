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
            # Definition request object
            request = urllib2.Request(url)  
    #        uid=2590&msg=%E4%BD%A0%E5%A5%BD+%E5%88%98%E6%97%B6%E5%98%89%EF%BC%81&msgid=53970002&cmd=send&psw=CEE712A91DD4D0A8A67CC8E47B645662&mobiles=15010955397
            request.add_data(urllib.urlencode(data))
            request.add_header("Content-type", "application/x-www-form-urlencoded")
            
            # Definition connect times
            tries = 3
            response = None
            while tries:  
                try:
                    # Open the page to obtain response object
                    response = urllib2.urlopen(request)  
                    break
                except HTTPError, msg:
                    logging.exception("Connection sms service HTTPError : %s", msg)
                    tries = tries - 1  
                    if tries:  
                        continue
                except URLError, msg:
                    logging.exception("Connection sms service URLError : %s", msg)
                    tries = tries - 1  
                    if tries:  
                        continue
                except Exception, msg:  
                    logging.exception("Connection sms service exception : %s", msg)
                    tries = tries - 1  
                    if tries:  
                        continue
        
            if response:
                # Get response message header  
                headerObject = response.headers  
                # Get response text  
                streamData = "" 
                while True:  
                    subData = response.read(2048)  
                    if subData == "":  
                        break  
                    streamData = streamData + subData  
            
                # Judge returns the page code mechanism  
                if headerObject.has_key('Content-Encoding'):  
                    if cmp(headerObject['Content-Encoding'].strip().upper(), 'gzip'.upper()) == 0:  
                        compresseddata = streamData  
                        compressedstream = StringIO.StringIO(compresseddata)  
                        gzipper = gzip.GzipFile(fileobj=compressedstream)  
                        htmlCode = gzipper.read()
                    else:  
                        htmlCode = streamData  
                else:  
                    # Get back to the page content  
                    htmlCode = streamData  
    #            print dir(headerObject)
    #            print dict(headerObject)
    #            print dir(response)
    #            print response.__dict__
                # Judge returns the content of the page code, and transformed into utf-8 encoding
                if headerObject.has_key('content-type'):  
                    contentType = headerObject['content-type']
                    # If there is a 'charset =' the string
                    if contentType.lower().find('charset=') != -1:  
                        charset = re.search(r'charset=([^;]*)', contentType.lower()).group(1)
                        if charset != encoding:  
                            try:  
                                htmlCode = htmlCode.decode(charset)
                            except:
                                logging.exception("Encoding return message exception : %s", msg)
            else:
                logging.error("Connection response is None")
                htmlCode = None
                
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
                msg=u"你好 ！".encode('gbk')
                )
    htmlCode = send_http_post_request(data)
    print htmlCode
