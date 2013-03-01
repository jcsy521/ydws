# -*- coding:utf-8 -*-

import os.path
DOWNLOAD_DIR_ = os.path.abspath(os.path.join(__file__, "../../../apps/uweb/static/download/"))

from xml.dom import minidom
from utils.dotdict import DotDict


def get_version_info(tag):
    """Get info about version.
    """
    xml = minidom.parse(os.path.join(DOWNLOAD_DIR_,"download.xml"))
    version = xml.getElementsByTagName(tag)
    version_code = version[0].getElementsByTagName('versioncode') 
    version_name = version[0].getElementsByTagName('versionname')
    version_info = version[0].getElementsByTagName('versioninfo')
    version_updatetime = version[0].getElementsByTagName('updatetime')
    version_filesize = version[0].getElementsByTagName('filesize')
    versioncode = version_code[0].firstChild.data if version_code[0].firstChild else ''
    versionname = version_name[0].firstChild.data if version_name[0].firstChild else '' 
    versioninfo = version_info[0].firstChild.data if version_info[0].firstChild else '' 
    updatetime = version_updatetime[0].firstChild.data if version_updatetime[0].firstChild else '' 
    filesize = version_filesize[0].firstChild.data if version_filesize[0].firstChild else '' 

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
