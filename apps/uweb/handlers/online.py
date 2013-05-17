# -*- coding: utf-8 -*-

from os import SEEK_SET
import datetime, time
import logging
import hashlib

import tornado.web
from tornado.escape import json_decode, json_encode

from base import BaseHandler, authenticated
from constants import EXCEL, UWEB
from codes.errorcode import ErrorCode
from utils.dotdict import DotDict


class OnlineHandler(BaseHandler):
    
    KEY_TEMPLATE = "online_report_%s_%s"
    
    @authenticated
    @tornado.web.removeslash
    def post(self):
        status = ErrorCode.SUCCESS
        try:
            data = DotDict(json_decode(self.request.body))
            page_size = UWEB.LIMIT.PAGE_SIZE
            page_number = int(data.pagenum)
            page_count = int(data.pagecnt)
            start_time= data.start_time
            end_time = data.end_time
        except Exception as e:
            logging.exception("[UWEB] cid:%s, oid:%s search online statistic data format illegal. Exception: %s",
                              self.current_user.cid, self.current_user.oid, e.args)
            status = ErrorCode.ILLEGAL_DATA_FORMAT
            self.write_ret(status)
            return
        
        try:
            m = hashlib.md5()
            m.update(self.request.body)
            hash_ = m.hexdigest()
            mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)
            data = self.redis.getvalue(mem_key)
            if data:
                self.write_ret(status, 
                               dict_=DotDict(res=data[0],
                                             pagecnt=data[2],
                                             hash_=hash_))
                return
            
            statistic = self.db.get("SELECT count(id) AS count"
                                    "  FROM T_ONLINE_STATISTIC"
                                    "  WHERE time BETWEEN %s AND %s"
                                    "  AND cid = %s",
                                    start_time, end_time, self.current_user.cid)
            
            if page_count == -1:
                count = statistic.count
                d, m = divmod(count, page_size)
                page_count = (d + 1) if m else d
                
            res = self.db.query("SELECT online_num, offline_num, time, (online_num + offline_num) AS total_num"
                                "  FROM T_ONLINE_STATISTIC"
                                "  WHERE time BETWEEN %s AND %s"
                                "  AND cid = %s"
                                "  ORDER BY time DESC"
                                "  LIMIT %s, %s",
                                start_time, end_time, self.current_user.cid, 
                                page_number * page_size, page_size)
            
            for i, result in enumerate(res):
                    result['seq'] = i + 1
                    for key in result:
                        if result[key] is None:
                            result[key] = ''
            
            interval = [start_time, end_time]
            self.redis.setvalue(mem_key,(res, interval, page_count), 
                                time=UWEB.STATISTIC_INTERVAL)
            self.write_ret(status,
                           dict_=DotDict(res=res,
                                         pagecnt=page_count,
                                         hash_=hash_))
            
        except Exception as e:
            logging.exception("[UWEB] cid:%s, oid:%s search online statistic failed. Exception: %s",
                              self.current_user.cid, self.current_user.oid, e.args)
            status = ErrorCode.SERVER_BUSY
            self.write_ret(status)
        

class OnlineDownloadHandler(OnlineHandler):

    @authenticated
    @tornado.web.removeslash
    def get(self):
        status = ErrorCode.SUCCESS
        hash_ = self.get_argument('hash_', None)
        mem_key = self.KEY_TEMPLATE % (self.current_user.uid, hash_)
        r = self.redis.getvalue(mem_key)
        if r:
            results, start_time, end_time = r[0], r[1][0], r[1][1]
        else:
            logging.exception("[UWEB] online statistic export excel failed, find no res by hash_:%s", hash_)
            self.render("error.html",
                        message=ErrorCode.ERROR_MESSAGE[ErrorCode.EXPORT_FAILED],
                        home_url=ConfHelper.UWEB_CONF.url_out)
            return

        import xlwt
        from cStringIO import StringIO

        date_style = xlwt.easyxf(num_format_str='YYYY-MM-DD HH:mm:ss')
        
        wb = xlwt.Workbook()
        ws = wb.add_sheet(EXCEL.OLINE_SHEET)

        start_line = 0
        for i, head in enumerate(EXCEL.OLINE_HEADER):
            ws.write(0, i, head)

        start_line += 1
        for i, result in zip(range(start_line, len(results) + start_line), results):
            t = time.strftime("%Y%m%d", time.localtime(int(result['time'])))
            online_time = t[:4] + u'年' + t[4:6] + u'月' + t[6:8] + u'日 '
            ws.write(i, 0, online_time)
            ws.write(i, 1, result['online_num'])
            ws.write(i, 2, result['offline_num'])
            ws.write(i, 3, result['total_num'])
            
        _tmp_file = StringIO()
        wb.save(_tmp_file)
        filename = self.generate_file_name(EXCEL.OLINE_FILE_NAME)
        if start_time:
            s_time = time.strftime("%Y%m%d", time.localtime(start_time))
            e_time = time.strftime("%Y%m%d", time.localtime(end_time))
            filename = s_time[:4] + u'年' + s_time[4:6] + u'月' + s_time[6:] + u'日--' + e_time[:4] + u'年' + e_time[4:6] + u'月' + e_time[6:] + u'日' + filename

        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s.xls' % (filename,))

        # move the the begging. 
        _tmp_file.seek(0, SEEK_SET)
        self.write(_tmp_file.read())
        _tmp_file.close()
