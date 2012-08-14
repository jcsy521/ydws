# -*- coding: utf-8 -*-

from time import time, mktime
import datetime
import logging

from tornado.ioloop import IOLoop

from utils.dotdict import DotDict
from utils.misc import get_terminal_time, get_name_cache_key, get_ssdw_sms_key
from codes.errorcode import ErrorCode
from codes.smscode import SMSCode
from helpers.queryhelper import QueryHelper
from helpers.smshelper import SMSHelper
from constants import PLAN, REMOTE_EVENT, SCHEDULE, SMS
from constants.REALTIME import REALTIME_VALID_INTERVAL

from errors.smserror import SMSException
from errors.updateerror import UpdateException, DataBaseException
from mixin.realtime import RealtimeMixin
from mixin.remoteevent import RemoteEventMixin
from mixin.schedule import ScheduleMixin

from uwebtasks import check_sms_realtime

    
class BaseCallback(object):
    def __init__(self, pmobile, packet, db, redis):
        # parent's mobile
        self.pmobile = pmobile
        # what the parent sent via sms
        self.packet = packet
        self.db = db
        self.redis = redis

    
class RealtimeCallback(BaseCallback, RealtimeMixin):

    _STANDARD_PACKET_COMPONENTS_NUM = 2
    _SIMPLE_PACKET_COMPONENTS_NUM = 1

    def __init__(self, pmobile, packet, db, redis):
        BaseCallback.__init__(self, pmobile, packet, db, redis)
        
    def __check(self):
        """@param
               standard : 
                   <packet> = SSDW <target>
               simple : 
                   <packet> = SSDW
        """

        packet_parts = self.packet.split()
        
        if len(packet_parts) == self._STANDARD_PACKET_COMPONENTS_NUM:
            self.sim = packet_parts[1]
            r = QueryHelper.get_monitor_relation(self.pmobile, self.sim, self.db)
            if r:
                self.xxt_uid, self.xxt_tid = r.xxt_uid, r.xxt_tid
            else:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.NO_PRIVILEGE])
        elif len(packet_parts) == self._SIMPLE_PACKET_COMPONENTS_NUM:
            r = QueryHelper.get_monitor_relation_by_pmobile(self.pmobile, self.db)
            if len(r) == 1:
                self.xxt_uid, self.xxt_tid = r[0].xxt_uid, r[0].xxt_tid
                self.sim = r[0].mobile
            elif len(r) > 1:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.SSDW_MULTI_CHILD_MOBILES])
            elif r.num == 0:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.NO_PRIVILEGE])
            else:
                pass
        else:
            raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.SSDW_FORMAT_ERROR])

    def handle(self):
        self.__check()
        category = self.get_category_by_sim(self.sim)
        if category in (PLAN.TERMINAL_CATEGORY.ESPECIAL_NO_GPS_TERMINAL, PLAN.TERMINAL_CATEGORY.GENERAL_TERMINAL):
            flag = 1
        else:
            flag = 0
        query = DotDict(timestamp=int(time() * 1000), # in milliseconds
                        mobile=self.pmobile,
                        flag=flag)

        sms_key = get_ssdw_sms_key(self.sim)
        flag = self.redis.getvalue(sms_key)
        if flag:
            location = self.redis.getvalue(str(self.sim))
            if location and abs(time() * 1000 - location.timestamp) > REALTIME_VALID_INTERVAL:
                location = None
            if location:
                terminal_time = get_terminal_time(int(location.timestamp))
                xxt_key = get_name_cache_key(self.sim)
                xxt_name = self.redis.getvalue(xxt_key) or ""
                realtime_result = SMSCode.SMS_REALTIME_RESULT % (xxt_name, location.name, terminal_time)
                SMSHelper.send(self.pmobile, realtime_result)
                self.redis.delete(sms_key)
            else:
                SMSHelper.send(self.pmobile, SMSCode.SMS_REALTIME_WARNING)

            return
        else:
            self.redis.setvalue(sms_key, True, REALTIME_VALID_INTERVAL / 1000)

        def _on_finish(realtime):
            realtime_result = None
            if realtime.status != ErrorCode.SUCCESS:
                if realtime.status in (ErrorCode.GPRS_TERMINAL_OFFLINE, ErrorCode.TERMINAL_TIME_OUT):
                    check_sms_realtime(self.sim, new_created=False)
                else:
                    realtime_result = realtime.message
            else:
                if realtime.location:
                    if len(realtime.location.name.strip()) == 0:
                        realtime_result = SMSCode.SMS_REALTIME_RESULT % ErrorCode.ERROR_MESSAGE[ErrorCode.LOCATOIN_NAME_NONE]
                    else:
                        terminal_time = get_terminal_time(int(realtime.location.timestamp))
                        key = get_name_cache_key(self.sim)
                        xxt_name = self.redis.getvalue(key) or ""
                        realtime_result = SMSCode.SMS_REALTIME_RESULT % (xxt_name, realtime.location.name, terminal_time)
                else:
                    check_sms_realtime(self.sim)
            if realtime_result:
                self.redis.delete(sms_key)
                SMSHelper.send(self.pmobile, realtime_result)

        # this contains async_forward, so use callback.
        self.request_realtime(self.xxt_uid, self.sim, query,
                              callback=_on_finish)
        return None


class ScheduleCallback(BaseCallback, ScheduleMixin):
    """
    create a schedule query plan via sms.
    """

    _STANDARD_PACKET_COMPONENTS_NUM = 3
    _SIMPLE_PACKET_COMPONENTS_NUM = 2

    def __init__(self, pmobile, packet, db, redis):
        BaseCallback.__init__(self, pmobile, packet, db, redis)
        self.retry_flag = 0
 
    def __check(self):
        """@param
            standard :
                <packet> = DSDW <target> <HHmm>
            simple :
                <packet> = DSDW <HHmm>
        """
        packet_parts = self.packet.split()

        res = [] 
        if len(packet_parts) == self._STANDARD_PACKET_COMPONENTS_NUM:
            self.__check_time(packet_parts[2])
            self.sim = packet_parts[1]
            r = QueryHelper.get_monitor_relation(self.pmobile, self.sim, self.db)
            if r:
                category = self.get_category_by_sim(self.sim)
                if category != PLAN.TERMINAL_CATEGORY.GENERAL_TERMINAL:
                    self.xxt_uid, self.xxt_tid = r.xxt_uid, r.xxt_tid
                    res = self.__check_limit()
                else:
                    raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.NO_THIS_FUNCTION])
            else:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.NO_PRIVILEGE])
        elif len(packet_parts) == self._SIMPLE_PACKET_COMPONENTS_NUM:
            r = QueryHelper.get_monitor_relation_by_pmobile(self.pmobile, self.db)
            if not r:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.NO_PRIVILEGE])
            targets = []
            for i, item in enumerate(r):
                category = self.get_category_by_sim(r[i].mobile)
                if category != PLAN.TERMINAL_CATEGORY.GENERAL_TERMINAL:
                    item['category'] = category
                    targets.append(item)
            if len(targets) == 0:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.NO_THIS_FUNCTION])
            elif len(targets) == 1: 
                self.__check_time(packet_parts[1])
                self.xxt_uid, self.xxt_tid = targets[0].xxt_uid, targets[0].xxt_tid
                self.sim = targets[0].mobile
                res = self.__check_limit()
            elif len(targets) == 2:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.DSDW_MULTI_CHILD_MOBILES])
            else:
                pass
        else:
            raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.DSDW_FORMAT_ERROR])

        return res
        
    def __check_time(self, hhmm):
        if len(hhmm) != 4:
            raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.DSDW_TIME_FORMAT_ERROR])
        try:
            hour = int(hhmm[:2])
            minute = int(hhmm[-2:])
            if hour < 0 or hour > 24 or minute < 0 or minute > 59:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.DSDW_TIME_FORMAT_ERROR])
        except ValueError:
            raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.DSDW_TIME_FORMAT_ERROR])
        except:
            raise
        
        # use localtime first
        begin_time = datetime.datetime.combine(datetime.datetime.now().date(),
                                               datetime.time(hour, minute))
        end_time = begin_time + datetime.timedelta(days=30)
        # convert to utc epoch
        f = lambda t: int(mktime(t.timetuple()) * 1000)
        self.begin_time, self.end_time = map(f, (begin_time, end_time))

    def __check_limit(self):
        """If you have reached the upbound.
        """
        res = self.get_valid_schedules(self.sim)
        if len(res) >= SCHEDULE.LIMIT:
            raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.SCHEDULE_REACH_LIMIT])

        return res

    def handle(self):
        res = self.__check()
        seqs = [int(r.seq) for r in res]
        seq = min(set([1,2,3]) - set(seqs))
        schedules = DotDict(start_time=self.begin_time,
                            end_time=self.end_time,
                            check_freq=60 * 60 * 24,
                            seq=str(seq))

        status = ErrorCode.SUCCESS
        message = None 
        try:
            response = self.insert_schedules(self.sim, schedules)
        except UpdateException as e:
            logging.error("[SMS] Error: %s, Sim: %s", e.args[0], self.sim)
            if self.retry_flag == 0:
                IOLoop.instance().add_timeout(int(time()) + 60,
                                              lambda: self.handle())
                self.retry_flag = 1
                return
            status = ErrorCode.FLUSH_SCHEDULE_QUERY_PLAN_FAILED
            message = e.args[0] if e.args[0] else ErrorCode.ERROR_MESSAGE[status]
        except DataBaseException as e:
            logging.error("[SMS] Error: %s, Sim: %s", e.args[0], self.sim)
            status = ErrorCode.FLUSH_SCHEDULE_QUERY_PLAN_FAILED
        except Exception as e:
            logging.exception("[SMS] Error: %s, Sim: %s", e.args, self.sim)
            status = ErrorCode.FLUSH_SCHEDULE_QUERY_PLAN_FAILED

        message = message if message else ErrorCode.ERROR_MESSAGE[status]
        if message:
            SMSHelper.send(self.pmobile, message)

        return None


class RemoteEventCallback(BaseCallback, RemoteEventMixin):
    """Handle all parent requests for remote actions, such as remote
       listen, remote poweroff and remote poweron.
    """
    
    _STANDARD_PACKET_COMPONENTS_NUM = 2
    _SIMPLE_PACKET_COMPONENTS_NUM = 1
    
    def __init__(self, pmobile, packet, db, redis):
        BaseCallback.__init__(self, pmobile, packet, db, redis)
        self.retry_flag = 0
 
    def __check(self):
        """@param
            standard :
                <packet> = YCHB <target>
                <packet> = YCKJ <target>
                <packet> = YCGJ <target>
            simple :
                <packet> = YCHB
                <packet> = YCGJ
        """

        packet_parts = self.packet.split()
        self.command = packet_parts[0]
        
        if len(packet_parts) == self._STANDARD_PACKET_COMPONENTS_NUM:
            self.sim = packet_parts[1]
            
            r = QueryHelper.get_monitor_relation(self.pmobile, self.sim, self.db)
            if r:
                category = self.get_category_by_sim(self.sim)
                if category != PLAN.TERMINAL_CATEGORY.GENERAL_TERMINAL:
                    self.xxt_uid, self.xxt_tid = r.xxt_uid, r.xxt_tid
                else:
                    raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.NO_THIS_FUNCTION])
            else:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.NO_PRIVILEGE])
            try:
                self.category = REMOTE_EVENT.CATEGORY[self.command.upper()]
            except KeyError:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.ILLEGAL_COMMAND_FORMAT])
            
        elif len(packet_parts) == self._SIMPLE_PACKET_COMPONENTS_NUM:
            r = QueryHelper.get_monitor_relation_by_pmobile(self.pmobile, self.db)
            if not r:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.NO_PRIVILEGE])
            targets = []
            for i, item in enumerate(r):
                category = self.get_category_by_sim(r[i].mobile)
                if category != PLAN.TERMINAL_CATEGORY.GENERAL_TERMINAL:
                    item['category'] = category
                    targets.append(item)
            if len(targets) == 0:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.NO_THIS_FUNCTION])
            elif len(targets) == 1: 
                self.xxt_uid, self.xxt_tid = targets[0].xxt_uid, targets[0].xxt_tid
                self.sim = targets[0].mobile
                try:
                    self.category = REMOTE_EVENT.CATEGORY[self.command.upper()]
                except KeyError:
                    raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.ILLEGAL_COMMAND_FORMAT])
            elif len(targets) == 2:
                if self.command.upper() == REMOTE_EVENT.COMMAND.YCHB:
                    raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.YCHB_MULTI_CHILD_MOBILES])
                elif self.command.upper() == REMOTE_EVENT.COMMAND.YCGJ:
                    raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.YCGJ_MULTI_CHILD_MOBILES])
                else:
                    raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.ILLEGAL_COMMAND_FORMAT]) 
            else:
                pass
        else:
            if self.command.upper() == REMOTE_EVENT.COMMAND.YCHB:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.YCHB_FORMAT_ERROR])
            elif self.command.upper() == REMOTE_EVENT.COMMAND.YCGJ:
                raise SMSException(ErrorCode.ERROR_MESSAGE[ErrorCode.YCGJ_FORMAT_ERROR])
            else:
                pass

    def handle(self):
        self.__check()
        query = DotDict(timestamp=int(time() * 1000), # in milliseconds
                        mobile=self.pmobile,
                        category=self.category)
        def _on_finish(response):
            if response['success'] != 0:
                if response['success'] in (ErrorCode.TERMINAL_OFFLINE, ErrorCode.TERMINAL_TIME_OUT):
                    if self.retry_flag == 0:
                        IOLoop.instance().add_timeout(int(time()) + 60,
                                                      lambda: self.handle())
                        self.retry_flag = 1
                        return
                if self.category == REMOTE_EVENT.CATEGORY.YCHB:
                    status = ErrorCode.REMOTE_YCHB_FAILED
                elif self.category == REMOTE_EVENT.CATEGORY.YCGJ:
                    status = ErrorCode.REMOTE_YCGJ_FAILED
                else:
                    status = ErrorCode.FAILED 
                info = response['info']
                message = info if info else ErrorCode.ERROR_MESSAGE[status]
                logging.error("Error: %s, Sim: %s", message, self.sim)
                SMSHelper.send(self.pmobile, message)
        self.request_remote(self.xxt_uid, self.sim, query,
                            callback=_on_finish)
        return None


_DISPATCHER = {
    # request handlers: monitor -> platform
    REMOTE_EVENT.COMMAND.SSDW: RealtimeCallback,     # realtime query
    REMOTE_EVENT.COMMAND.DSDW: ScheduleCallback,     # schedule query
    REMOTE_EVENT.COMMAND.YCHB: RemoteEventCallback,  # remote listen
    REMOTE_EVENT.COMMAND.YCKJ: RemoteEventCallback,  # remote power on
    REMOTE_EVENT.COMMAND.YCGJ: RemoteEventCallback,  # remote power off
    }


def process(mobile, packet, db, redis):
    try:
        action = packet.split()[0].upper()
        callback = _DISPATCHER[action](mobile, packet, db, redis)
        response = callback.handle()
    except KeyError as e:
        return ErrorCode.ERROR_MESSAGE[ErrorCode.UNKNOWN_COMMAND]
    except SMSException as e:
        return e.args[0]
    except Exception as e:
        logging.exception("sms process error: %s, mobile: %s",
                          e.args, mobile)
        return None
    else:
        return response
