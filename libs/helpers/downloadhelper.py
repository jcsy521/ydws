# -*- coding:utf-8 -*-

import os.path
DOWNLOAD_DIR_ = os.path.abspath(os.path.join(__file__, "../../../apps/uweb/static/download/"))

from  xml.dom import minidom
from utils.dotdict import DotDict


def get_version_info(category):
    """Get info about version.
    """
    # NOTE: here, just hande android
    xml = minidom.parse(os.path.join(DOWNLOAD_DIR_,"download.xml"))
    android = xml.getElementsByTagName(category)
    android_code = android[0].getElementsByTagName('versioncode') 
    android_name = android[0].getElementsByTagName('versionname')
    android_info = android[0].getElementsByTagName('versioninfo')
    android_updatetime = android[0].getElementsByTagName('updatetime')
    android_filesize = android[0].getElementsByTagName('filesize')
    versioncode = android_code[0].firstChild.data
    versionname = android_name[0].firstChild.data
    versioninfo = android_info[0].firstChild.data
    updatetime = android_updatetime[0].firstChild.data
    filesize = android_filesize[0].firstChild.data

    return DotDict(versioncode=versioncode,
                   versionname=versionname,
                   versioninfo=versioninfo,
                   updatetime=updatetime,
                   filesize=filesize)

def get_download_count(category, db):
    """Get the last times of downloading.
    """
    download = db.get("SELECT count FROM T_DOWNLOAD"
                      "  WHERE category = %s"
                      "  LIMIT 1",
                      category)
    return download
    
def update_download_count(category, db):
    """When someone makes a downlaod, increase count by 1.
    """
    db.execute("UPDATE T_DOWNLOAD"
               "  SET count = count+1"
               "  WHERE category = %s",
               category)
