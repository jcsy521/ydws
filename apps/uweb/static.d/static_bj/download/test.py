from  xml.dom import minidom
import re


if __name__ == '__main__':
    xml = minidom.parse("keys.xml")
    android = xml.getElementsByTagName('android')
    app_key = android[0].getElementsByTagName('app_key')[0].firstChild.data
    secret = android[0].getElementsByTagName('secret')[0].firstChild.data
    begintime = android[0].getElementsByTagName('begintime')[0].firstChild.data
    endtime = android[0].getElementsByTagName('endtime')[0].firstChild.data
    print app_key, secret, begintime, endtime
    
