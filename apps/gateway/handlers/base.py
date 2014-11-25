
import pika
import json
import time
import logging

from clw.packet.parser.codecheck import T_CLWCheck 
from clw.packet.composer.async import AsyncRespComposer
from gf.packet.composer.uploaddatacomposer import UploadDataComposer


from helpers.queryhelper import QueryHelper

from utils.dotdict import DotDict

from constants import EVENTER, GATEWAY, UWEB, SMS

from handlers import (login, acc, config, defend, fob, heartbeat, locationdesc, misc, runtime, sleep, unbind, unusual)

from handlers.basic import append_gw_request, append_si_request, get_resend_flag, update_terminal_status

from utils.misc import get_acc_status_info_key

from error import GWException

class Base(object):
    """Handle the packets.
    """

    def __init__(self, db, redis, exchange, gw_binding, si_binding): 
        self.db = db 
        self.redis = redis 
        self.exchange = exchange 
        self.gw_binding = gw_binding 
        self.si_binding = si_binding

    def handle_packets_from_terminal(self, packets, address, connection, channel, name):
        """Handle packets recv from terminal:

        """
        packets = self.divide_packets(packets)
        for packet in packets:
            clw = T_CLWCheck(packet)
            if not clw.head:
                break
            #TODO: db is unwanted.
            self.handle_packet(clw, address, connection, channel, name, packet, self.db)

    def divide_packets(self, packets):
        """Divide multi-packets into a list, that contains valid packet.

        @param: multi-packets
        @return: valid_packets
        """
        valid_packets = []

        while len(packets) > 0:
            start_index = packets.find('[')
            end_index = packets.find(']')
            if start_index == -1 or end_index == -1:
                logging.error("[GW] Invalid packets:%s", packets)
                packets = ''
            elif end_index < start_index:
                logging.error("[GW] Invalid packets:%s", packets[:start_index])
                packets = packets[start_index:]
            else:
                packet = packets[start_index:end_index+1]
                tmp_index = packet[1:].rfind('[')
                if tmp_index != -1:
                    logging.error("[GW] Invalid packets:%s", packets[:tmp_index])
                    packet = packet[tmp_index:]
                valid_packets.append(packet)
                packets = packets[end_index+1:]

        return valid_packets
 
    def handle_packet(self, clw, address, connection, channel, name, packet, db):
        """Main mehtod. 
        Handle packet from terminal.
        T1~T31
        """
        command = clw.head.command
        request = None
        if command == GATEWAY.T_MESSAGE_TYPE.LOGIN: # T1
            logging.info("[GW] Thread%s recv login packet:\n%s", name, packet)
            login.handle_login(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis) 
        elif command == GATEWAY.T_MESSAGE_TYPE.HEARTBEAT: # T2
            logging.info("[GW] Thread%s recv heartbeat packet:\n%s", name, packet)
            heartbeat.handle_heartbeat(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.LOCATIONDESC: # T10
            logging.info("[GW] Thread%s recv locationdesc packet:\n%s", name, packet)
            locationdesc.handle_locationdesc(clw, address, connection, channel, self.exchange, self.gw_binding,  db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.CONFIG: # T17
            logging.info("[GW] Thread%s recv query config packet:\n%s", name,  packet)
            config.handle_config(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.DEFENDSTATUS: # T18, #NOTE: deprecated
            logging.info("[GW] Thread%s recv defend status packet:\n%s", name, packet)
            defend.handle_defend(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.FOBINFO: # T19 #NOTE: deprecated 
            logging.info("[GW] Thread%s recv fob info packet:\n%s", name, packet)
            fob.handle_fob_info(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.SLEEPSTATUS: # T21
            logging.info("[GW] Thread%s recv sleep status packet:\n%s", name, packet)
            sleep.handle_sleep(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.FOBSTATUS: # T22, #NOTE: deprecated
            logging.info("[GW] Thread%s recv fob status packet:\n%s", name, packet)
            fob.handle_fob_status(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.RUNTIMESTATUS: # T23
            logging.info("[GW] Thread%s recv runtime status packet:\n%s", name, packet)
            runtime.handle_runtime(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.UNBINDSTATUS: # T24
            logging.info("[GW] Thread%s recv unbind status packet:\n%s", name, packet)
            unbind.handle_unbind_status(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.UNUSUALACTIVATE: # T27
            logging.info("[GW] Thread%s recv unusual activate packet:\n%s", name, packet)
            unusual.handle_unusual(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.MISC: # T28
            logging.info("[GW] Thread%s recv misc packet:\n%s", name, packet)
            misc.handle_misc(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.ACC_STATUS: # T30
            logging.info("[GW] Thread%s recv power status packet:\n%s", name, packet)
            acc.handle_acc_status(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        elif command == GATEWAY.T_MESSAGE_TYPE.ACC_STATUS_REPORT: # T31
            logging.info("[GW] Thread%s recv power status report packet:\n%s", name, packet)
            acc.handle_acc_status_report(clw, address, connection, channel, self.exchange, self.gw_binding, db, self.redis)
        else: #NOTE: otherswill be forwar to SI server
            #(T13, T14, T15, T16, T26, T29) 
            logging.info("[GW] Thread%s recv packet from terminal:\n%s", name, packet)
            self.foward_packet_to_si(clw, packet, address, connection, channel, db)

    def foward_packet_to_si(self, info, packet, address, connection, channel, db):
        """
        Response packet or position/report/charge packet

        0: success, then forward it to SIServer and record new terminal's address
        1: invalid SessionID 
        """
        try:
            head = info.head
            args = DotDict(success=GATEWAY.RESPONSE_STATUS.SUCCESS,
                           command=head.command)
            dev_id = head.dev_id
            resend_key, resend_flag = get_resend_flag(self.redis, dev_id, head.timestamp, head.command)
            sessionID = QueryHelper.get_terminal_sessionID(dev_id, self.redis)
            if sessionID != head.sessionID:
                args.success = GATEWAY.RESPONSE_STATUS.INVALID_SESSIONID
                logging.error("[GW] Invalid sessionID, Terminal: %s", dev_id)
            else:
                seq = str(int(time.time() * 1000))[-4:]
                uargs = DotDict(seq=seq,
                                dev_id=dev_id,
                                content=packet)
                content = UploadDataComposer(uargs).buf
                logging.info("[GW] Forward message to SI:\n%s", content)
                if resend_flag:
                    logging.warn("[GW] Recv resend packet: %s, and drop it!", packet)
                else:
                    append_si_request(content, connection, channel, self.exchange, self.si_binding)
                update_terminal_status(self.redis, dev_id, address)

            #NOTE: Handle the packet.
            if head.command in (GATEWAY.T_MESSAGE_TYPE.POSITION, GATEWAY.T_MESSAGE_TYPE.MULTIPVT,
                                GATEWAY.T_MESSAGE_TYPE.CHARGE, GATEWAY.T_MESSAGE_TYPE.ILLEGALMOVE,
                                GATEWAY.T_MESSAGE_TYPE.POWERLOW, GATEWAY.T_MESSAGE_TYPE.ILLEGALSHAKE,
                                GATEWAY.T_MESSAGE_TYPE.EMERGENCY, GATEWAY.T_MESSAGE_TYPE.POWERDOWN, 
                                GATEWAY.T_MESSAGE_TYPE.STOP):
                logging.info("[GW] Head command: %s.", head.command)
                if args['success'] == GATEWAY.RESPONSE_STATUS.SUCCESS: 
                    acc_status_info_key = get_acc_status_info_key(dev_id) 
                    acc_status_info = self.redis.getvalue(acc_status_info_key) 
                    if acc_status_info and (not acc_status_info['t2_status']): # T2(query) is need 
                        logging.info("[GW] ACC_status is changed, dev_id: %s, acc_status_info: %s", 
                                     dev_id, acc_status_info)
                        args['success'] = 3 # acc_status is changed

                #NOTE: composer response for terminal 
                rc = AsyncRespComposer(args)
                request = DotDict(packet=rc.buf,
                                  address=address,
                                  dev_id=dev_id)
              
                append_gw_request(request, connection, channel, self.exchange, self.gw_binding)
                # resend flag
                if not resend_flag:
                    self.redis.setvalue(resend_key, True, GATEWAY.RESEND_EXPIRY)
            elif head.command == GATEWAY.T_MESSAGE_TYPE.UNBIND: # S24-->T24
                logging.info("[GW] Head command: %s.", head.command)
                up = UNBindParser(info.body, info.head)
                status = up.ret['status']
                if status == GATEWAY.STATUS.SUCCESS:
                    delete_terminal(dev_id, db, self.redis)
            else:
                logging.exception("[GW] Invalid command: %s.", head.command)
        except:
            logging.exception("[GW] Handle SI message exception.")
            raise GWException
