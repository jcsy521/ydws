# -*- coding: utf-8 -*-

import logging

from xml.dom import Node
from base import BaseParser

class GvQueryParser(BaseParser):

    def __init__(self, message):
        BaseParser.__init__(self, message)
        self.is_success()

    def get_pointsinfo(self):
        pointsinfo = []
        try:
            if self.xml:
                Nodes = self.xml.getElementsByTagName("POIContext")
                for Node in Nodes:
                    pointinfo = dict({"ADDRESS":"", "NAME":"", "TEL":"", "clongitude":0, "clatitude":0})
                    pointNodes = Node.getElementsByTagName('POIInfo')
                    for pointNode in pointNodes:
                        for field in ("ADDRESS", "NAME", "TEL"):
                            if pointNode.attributes['name'].value == field:
                                pointinfo[field] = pointNode.attributes['value'].value
                    TELs = pointinfo["TEL"].split(";")
                    if len(TELs) > 2:
                        pointinfo["TEL"] = TELs[0] + u"；" + TELs[1]
                    posNode = Node.getElementsByTagName("pos")
                    if posNode:
                        lon_lat = posNode[0].childNodes[0].data
                        pointinfo['clongitude'] = float(lon_lat.split(" ")[0]) * 3600000
                        pointinfo['clatitude'] = float(lon_lat.split(" ")[1]) * 3600000
                    if not pointinfo['ADDRESS']:
                        placeNodes = Node.getElementsByTagName('Place')
                        for placeNode in placeNodes:
                            if placeNode.attributes['type'].value == 'Municipality':
                                city = placeNode.childNodes[0].data
                            elif placeNode.attributes['type'].value == 'CountrySubdivision':
                                province = placeNode.childNodes[0].data
                        if city == u'市辖区':
                            pointinfo['ADDRESS'] = province
                        else:
                            pointinfo['ADDRESS'] = city
                    pointsinfo.append(pointinfo)
        except Exception as e:
            logging.exception("GV: Parse points exception:%s", e.args[0]) 
        return pointsinfo 

    def is_success(self):
       
        if self.xml:
            errorNodes = self.xml.getElementsByTagName('Error')
            ServiceError = self.xml.getElementsByTagName('ServiceError')
            XMLError = self.xml.getElementsByTagName('XMLError')
            InfoNodes = ServiceError if ServiceError else XMLError
            
            if errorNodes:
                self.success = -1

            if InfoNodes:
                if "message" in InfoNodes[0].attributes.keys():
                    self.info = InfoNodes[0].attributes['message'].value        
