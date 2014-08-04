# -*- coding: utf-8 -*-

from sys import exit, stdout 
import socket 
import select 
import errno 
import logging
from time import sleep, time, strftime, localtime
import random
import struct

from gf.packet.composer.bindcomposer import BindComposer 
from gf.packet.composer.bindcomposer import UNBindComposer 
from gf.packet.composer.activetestcomposer import ActiveTestRespComposer 
from gf.packet.composer.uploaddatacomposer import UploadDataRespComposer 
from gf.packet.parser.codecheck import GFCheck 
from gf.packet.parser.uploaddataparser import UploadDataParser
from gf.packet.parser.sendparser import SendParser, SendRespParser

from clw.packet.parser.codecheck import T_CLWCheck, S_CLWCheck
from clw.packet.parser.async import AsyncParser

from utils.repeatedtimer import RepeatedTimer 
from utils.dotdict import DotDict 
from utils.misc import safe_unicode 
from constants import GF
from constants.GATEWAY import S_MESSAGE_TYPE
from codes.errorcode import ErrorCode
from helpers.seqgenerator import SeqGenerator 
from helpers.confhelper import ConfHelper 
from helpers.gfmessagehelper import GFMessageHelper


class LoginException(Exception):
    pass


class GFBase(object):
    """Base of GF.
    """

    # reconnect on these errors
    _RECONNECT_ERRORS = (errno.EPIPE, errno.ECONNRESET, errno.ESHUTDOWN,
                         errno.ECONNABORTED, errno.ENETRESET,
                         errno.EBADF, errno.EBADFD)


    # infinite retry count (big enough)
    MAX_RETRY_COUNT = 10000000

    def __init__(self, conf_file):
        ConfHelper.load(conf_file)
        for i in ('port', 'retry_interval', 'retry_count', 'recv_retry_count'):
            ConfHelper.GF_CONF[i] = int(ConfHelper.GF_CONF[i])

        self.__sock = None
        self.is_alive = False
        self.send_queue = None
        self.wait_response_queue = None
        self.last_check_time = None

        self.login()

    def __connect(self):
        """setup self.__sock."""
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        status = False

        if ConfHelper.GF_CONF.retry_count <= 0:
            ConfHelper.GF_CONF.retry_count = self.MAX_RETRY_COUNT

        def __wait():
            # interval = retry * ConfHelper.GF_CONF.retry_interval
            interval = ConfHelper.GF_CONF.retry_interval
            logging.error("[GFPROXY] Retry connecting in %d seconds.", interval)
            sleep(interval)

        for retry in xrange(ConfHelper.GF_CONF.retry_count):
            try:
                logging.info("[GFPROXY] Connecting GF...")
                self.__sock.connect((ConfHelper.GF_CONF.host, ConfHelper.GF_CONF.port))
            except:
                __wait()
            else:
                logging.info("[GFPROXY] GF connected.")
                status = True
                break
        if not status:
            logging.error("[GFPROXY] Connecting failed.")
        return status

    def login(self):
        if ConfHelper.GF_CONF.retry_count <= 0:
            ConfHelper.GF_CONF.retry_count = self.MAX_RETRY_COUNT

        def __wait():
            # interval = (2 ** retry) * ConfHelper.GF_CONF.retry_interval
            interval = ConfHelper.GF_CONF.retry_interval
            logging.error("[GFPROXY] Retry login in %d seconds.", interval)
            sleep(interval)

        go_ahead = False
        for retry in xrange(ConfHelper.GF_CONF.retry_count):
            self.__prepare_reconnect()
            if not self.__connect():
                continue

            logging.info("[GFPROXY] Login GF...")
            
            bc = BindComposer(dict(seq=str(random.randint(0, 9999)),
                                   username=ConfHelper.GF_CONF.username,
                                   password=ConfHelper.GF_CONF.password,
                                   time=strftime("%Y%m%d%H%M%S", localtime(time()))))
            try:
                self.send_request(bc.buf)
                response = self.recv_response()
            except Exception as e:
                response = ""
                logging.exception("[GFPROXY] Login GF error. reason: %s", e.args)
                __wait()
            else:
                gf = GFCheck(response)
                gfheads = gf.heads
                gfdatas = gf.datas
                for gfhead, gfdata in zip(gfheads, gfdatas):
                    command = gfhead.command
                    if command == '1001': # bind response
                        logging.info("bind_resp:\n%s", gfhead)
                        if gfhead.status == '0000':
                            logging.info("[GFPROXY] Login success!  status:%s", gfhead.status)
                            self.is_alive = True
                            go_ahead = True
                            break
                        else: 
                            logging.info("[GFPROXY] Login failed!  status:%s", gfhead.status)
                            __wait()
                    elif command == '0020': # active_test
                        logging.info("[GFPROXY] Active_test_resp:\n%s", gfhead)
                        args = DotDict(seq=gfhead.seq)
                        atc = ActiveTestRespComposer(args)
                        self.send_request(atc.buf)
                    else:
                        logging.exception("[GFPROXY] Unknown command:%s", command)
            if go_ahead:
                break
        if not self.is_alive:
            logging.error("[GFPROXY] Login failed.")
            self.__prepare_reconnect()
            raise LoginException("[GFPROXY] GF Login failed.")


    def logout(self):
        logging.info("[GFPROXY] Logout GF...")
        
        unbc = UNBindComposer(dict(seq=str(random.randint(0, 9999))))
        try:
            self.send_request(unbc.buf)
            go_ahead = False
            while True:
                response = self.recv_response()
                gf = GFCheck(response)
                gfheads = gf.heads
                gfdatas = gf.datas
                for gfhead, gfdata in zip(gfheads, gfdatas):
                    command = gfhead.command
                    if command == '1002': # unbind response
                        # NOTE: should check the response whether okay or nt
                        logging.info("[GFPROXY] unbind_resp:\n%s",gfhead)
                        if gfhead.status == '0000':
                            logging.info("[GFPROXY] logout success!  status:%s",gfhead.status)
                            go_ahead = True
                            self.destroy()
                            break
                        else: 
                            logging.info("[GFPROXY] logout failed!  status:%s",gfhead.status)
                    elif command == '0020': # active_test
                        logging.info("active_test_resp:\n%s", gfhead)
                        args = DotDict(seq=gfhead.seq)
                        atc = ActiveTestComposer(args)
                        self.send_request(atc.buf)
                    else:
                        logging.exception("unknown command:%s",command)
                if go_ahead:
                    break
            
        except:
            logging.exception("Logout GF error.")

    def reconnect(self):
        """This routine guarantee the application is reconnected to gf server,
        and the heartbeat thread is running, but nothing else. DO override this
        in the subclass if something else is required to do.
        """
        logging.debug("entering reconnect")
        if not self.is_alive:
            # this test is VERY important, otherwise, sender will reconnect several 
            # times.
            logging.warn("reconnecting gf...")
            self.__prepare_reconnect()
            try:
                self.login()
            except LoginException:
                logging.exception("Login failed.")
            except Exception as e:
                logging.exception("exception %s", e.args)
                
            if self.is_alive:
                logging.warn("gf reconnected.")
        else:
            logging.debug("someone has reconnected.")

    def send_request(self, request):
        """Send out a request to GF.
        
        @param request: a well formed GF request 

        @return: return value of socket.sendall()
        """
        try:
            self.__sock.sendall(request)
        except socket.error as e:
            logging.exception("socket send error: %s", e.args)
            if isinstance(e.args, tuple):
                if e[0] in self._RECONNECT_ERRORS:
                    self.__close_socket()
                    raise
        except AttributeError:
            self.__close_socket()
            raise socket.error(errno.EBADFD, "internal sock is reset.")
        except Exception as e:
            # TODO: this is dangerous!
            logging.exception("unknown send error: %s", e.args)
            
    def recv_all(self, length):
        """
        Circulation receiving packet until len(packet) == length
        avoid receiving half packet once.
        """
        ret_buf = ""

        while length:
            tmp_buf = self.__sock.recv(length)
            if not tmp_buf:
                logging.warn("[GFPROXY] recv empty response of socket!")
                self.__close_socket()
                raise socket.error(errno.EPIPE, "the pipe might be broken.") 
            ret_buf += tmp_buf 
            length -= len(tmp_buf)

        return ret_buf

    def recv_response(self):
        """ Get response from GF.
            workflow:
                get the length of packet first
                then recv left data of this packet
        """
        
        header_len = GF.len[GF.gftype['packet_len']]

        header = self.recv_all(header_len)
        packet_len = int(struct.unpack('!' + GF.fmt[GF.gftype['packet_len']], header)[0])
        body = self.recv_all(packet_len - header_len)
        packet = header + body 

        return packet 
            
    def _clear_wait_response_queue(self):
        logging.info("[GFPROXY] Clearing wait response queue: %s", len(self.wait_response_queue))
        try:
            for i in self.wait_response_queue:
                for j, item in enumerate(self.wait_response_queue[i]):
                    callback = item['callback']
                    success = ErrorCode.TERMINAL_TIME_OUT
                    info = ErrorCode.ERROR_MESSAGE[success]
                    callback(DotDict(success=success,info=info,clwdata=''))
        except Exception as e:
            logging.exception("callback error:%s", e.args)

        self.wait_response_queue.clear()

    def _clear_timeout_request(self):
        del_list = []
        if not self.last_check_time:
            self.last_check_time = time()

        if ((time() - self.last_check_time) < 10):
            return

        logging.info("[GFPROXY] Clearing timeout request in wait response queue.")
        self.last_check_time = time()
        for i in self.wait_response_queue:
            for j, item in enumerate(self.wait_response_queue[i]):
                callback = item['callback']
                insert_time = item['timestamp']
                if((time() - insert_time) < 30):
                    continue
                else:
                    del self.wait_response_queue[i][j]
                    try:
                        success = ErrorCode.TERMINAL_TIME_OUT
                        info = ErrorCode.ERROR_MESSAGE[success]
                        callback(DotDict(success=success,info=info,clwhead={},clwbody=''))
                    except Exception as e:
                        logging.exception("callback error: %s", e.args)
            if len(self.wait_response_queue[i]) == 0:
                del_list.append(i) 

        for item in del_list:
            del self.wait_response_queue[item]

    def periodic_send(self):
        """Send out request and receive the response.

        This should be guarded by the mutex, since the sock
        maybe shared by many clients.
        """
        while True: 
            # if there are some requests to be send, get one item from queue and
            # send it
            if self.send_queue.qsize() != 0:
                request = self.send_queue.get(True, 1)
                try:
                    self.send_request(request['packet'])

                    gf = GFCheck(request['packet']) 
                    gfhead = gf.heads[0]
                    # add the callback to wait response dict, and the key is seq number 
                    if request['callback']:
                        if gfhead.command == '0010':
                            sp = SendParser(gf.datas[0])
                            clw = S_CLWCheck(sp.gfbody.Content)
                            r_key = ("%s%s" % (sp.gfbody.Terminal_id, clw.head.command)).replace(' ','')
                            r_value = {'callback':request['callback'],
                                       'timestamp':time()}
                            if self.wait_response_queue.has_key(r_key):
                                self.wait_response_queue[r_key].append(r_value)
                            else:
                                self.wait_response_queue[r_key] = [r_value,]

                except socket.error as e:
                    logging.exception("sock error: %s", e.args)
                    # we need clear the wait response queue, avoid dead lock.
                    self._clear_wait_response_queue()
                    self.is_alive = False
                    self.reconnect()
                except Exception as e:
                    #TODO: can never see this
                    logging.exception("send error: %s", e.args)
                    response = ""

            # check whether there is some response to receive.  
            # if true, recv response as much as possible.(recv response is high priority)
            try:
                while(True):
                    infds, _, _ = select.select([self.__sock], [], [], 0.1)
                    if len(infds) > 0:
                        response = self.recv_response()
                        logging.info('[GFPROXY] Recv whole packet: %s', response)

                        gf = GFCheck(response)
                        gfheads = gf.heads
                        gfdatas = gf.datas

                        for gfhead, gfdata in zip(gfheads, gfdatas):
                            success, info = GFMessageHelper.format_gf_message(gfhead.status)
                            resp = DotDict(success=success,
                                           info=info,
                                           clwhead={},
                                           clwbody='')
                            if gfhead.command == '0020': # active_test, just give a response
                                logging.info("active_test_resp:\n%s", gfhead)
                                args = DotDict(seq=gfhead.seq)
                                atc = ActiveTestRespComposer(args)
                                self.send_request(atc.buf)
                            elif gfhead.command == '1010':
                                # NOTE: should check the response whether okay or nt
                                # if not 0000, callback
                                logging.info("send_data_resp\n%s, gfdata: %r", gfhead, gfdata)
                                srp = SendRespParser(gfdata)
                                is_reboot = (srp.gfbody.command.strip() == S_MESSAGE_TYPE.REBOOT)
                                if (is_reboot or (gfhead.status != '0000')):
                                    r_key = ("%s%s" % (srp.gfbody.Terminal_id, srp.gfbody.command)).replace(' ','')
                                    if self.wait_response_queue.has_key(r_key):
                                        callback = self.wait_response_queue[r_key][0]['callback']
                                        callback(resp)
                                        del self.wait_response_queue[r_key][0]
                                        if len(self.wait_response_queue[r_key]) == 0:
                                            del self.wait_response_queue[r_key]
                            elif gfhead.command == '0011': # upload_data
                                logging.info("upload_data\n%s, gfdata: %r", gfhead, gfdata)
                                args = DotDict(seq=gfhead.seq)
                                udrc = UploadDataRespComposer(args)
                                logging.info("upload_data_resp\n%r", udrc.buf)
                                self.send_request(udrc.buf)
                                # we got a response, and call the correspond callback, 
                                # and delete from wait response queue
                                udp = UploadDataParser(gfdata)
                                tc = T_CLWCheck(udp.content)
                                clwhead = tc.head
                                clwbody = tc.body

                                r_key = ("%s%s" % (clwhead.dev_id, 'S'+clwhead.command[1:])).replace(' ','')
                                if self.wait_response_queue.has_key(r_key):
                                    logging.info("[GFPROXY] UWEB-->GF-->UWEB. r_key: %s",
                                                 r_key)
                                    callback = self.wait_response_queue[r_key][0]['callback']
                                    resp.clwbody= clwbody
                                    resp.clwhead = clwhead
                                    callback(resp)
                                    del self.wait_response_queue[r_key][0]
                                    if len(self.wait_response_queue[r_key]) == 0:
                                        del self.wait_response_queue[r_key]
                                else:
                                    ap = AsyncParser(clwbody, clwhead)
                                    logging.info("[GFPROXY] SI-->GF-->EVENTER. ap.ret: %s",
                                                 ap.ret)
                                    if ap.ret:
                                        self.forward(ap.ret)
                                    else:
                                        logging.error("Unknow response received: %s, and drop it!",response)
                            else:
                                logging.exception("unknown command:%s", gfhead.command)

                    else:
                        break

                self._clear_timeout_request()
            except socket.error as e:
                logging.exception("sock error: %s", e.args)
                # we need clear the wait response queue, avoid dead lock.
                self._clear_wait_response_queue()
                self.is_alive = False
                self.reconnect()
                response = ""
            except Exception as e:
                #TODO: can never see this
                logging.exception("sock send error: %s", e.args)
                response = ""

    def __close_socket(self):
        try:
            self.__sock.close()
        except:
            pass

    def __prepare_reconnect(self):
        self.is_alive = False
        self.__close_socket()
        
    def destroy(self):
        # cleaning work, the same as before reconnecting.
        self.__prepare_reconnect()

    def __del__(self):
        self.destroy()
