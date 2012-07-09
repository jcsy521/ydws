# -*- coding: utf-8 -*-

from base import BaseComposer

class GvQueryComposer(BaseComposer):
    GV_BASE_TEMPLATE = u"""<?xml version="1.0" encoding="GB2312"?><!DOCTYPE Gis_Req SYSTEM "GIS_100.dtd"><Gis_Req Ver="1.0.0"><HDR Version="1.0.0"><Client><Id>%(username)s</Id><Pwd>%(password)s</Pwd><ServiceID>%(serviceid)s</ServiceID></Client><RequestorID>%(group)s</RequestorID></HDR>"""

    GV_POI_QUERY_TEMPLATE = u"""<DRR sortCriteria="Name" sortDirection="Ascending"><POILocation><Address countryCode="CN"><Place type="CountrySubdivision">%(province)s</Place><Place type="Municipality">%(city)s</Place><Place type="MunicipalitySubdivision">%(subdivision)s</Place></Address></POILocation><POIProperties directoryType="White Pages"><POIProperty name="Keyword" value="%(POIName)s"/></POIProperties><MaximumResponses>100</MaximumResponses></DRR></Gis_Req>"""

    GV_ROUND_QUERY_TEMPLATE = u"""<DRR><POILocation><WithinBoundary><AOI><CircleByCenterPoint interpolation="circularArcCenterPointWithRadius" numArc="1"><pos dimension="2" isEncrypted="false">%(lon)s %(lat)s</pos><radius uom="KM">%(r)</radius></CircleByCenterPoint></AOI></WithinBoundary></POILocation><POIProperties><POIProperty name="CUCS_Otype" value="%(cucs_type)s"/></POIProperties><MaximumResponses>100</MaximumResponses></DRR></Gis_Req>"""

    GV_RECT_QUERY_TEMPLATE = u"""<DRR><POILocation><WithinBoundary><AOI><Envelope><pos dimension="2" srsName="WGS-84" isEncrypted="false" msisdn="false">%(lon_left)s %(lat_left)s</pos><pos dimension="2" srsName="WGS-84" isEncrypted="false" msisdn="false">%(lon_right)s %(lat_right)s</pos></Envelope></AOI></WithinBoundary></POILocation><POIProperties><POIProperty name="CUCS_Otype" value="%(cucs_type)s"/></POIProperties></DRR></Gis_Req>"""    

    def __init__(self, args):
        import logging
        logging.info("args:%s", args)
        username = args['username']
        password = args['password']
        group = args['group']
        serviceid = args['serviceid'] 
        self.template = self.GV_BASE_TEMPLATE % locals()
        type = args['type']
        if type == "POI_QUERY":
            province = args['province']
            city = args['city']
            subdivision = args['subdivision']
            POIName = args['POIName']
            self.template += self.GV_POI_QUERY_TEMPLATE % locals()
        elif type == "ROUND_QUERY":
            lon = float(args['point'].lon)/3600000
            lat = float(args['point'].lat)/3600000
            r = args['radius']
            cucs_type = args['cucs_type']
            self.template += self.GV_ROUND_QUERY_TEMPLATE % locals()
        elif type == "RECT_QUERY":
            lon_left = args['points'][0]['lon']
            lat_left = args['points'][0]['lat']
            lon_right = args['points'][1]['lon']
            lat_right = args['points'][1]['lat']
            cucs_type = args['cucs_type']
            self.template += self.GV_RECT_QUERY_TEMPLATE % locals()
