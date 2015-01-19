/**
* ydcws-push.js
* hs
* 2014-9-2
**/
$(function () {
	var socketCon = null;
	
	//对相应终端进行追踪操作
	dlf.fn_initPushServices = function() {
		var str_pushId = $('#push_id').val(),
			str_pushKey = $('#push_key').val(),
			str_devid = $.cookie('YDCWSDEVID'),
			//str_basePushUrl = 'http://192.168.1.9:6412',
			// str_basePushUrl = 'http://jiaxiaolei.nat123.net:6412',
			str_bpushUrl = str_basePushUrl,
			str_pushUrl = '',
			b_isHttps = document.location.protocol == 'https:' ? true : false;
		
		if ( DOMAIN_HOST.search('ydcws.com') != -1 ) { 
			str_bpushUrl = str_baseYdcwsPushUrl;
		} else if ( DOMAIN_HOST.search('ichebao') != -1 ) { 
			str_bpushUrl = str_baseichebaoPushUrl;
		}
		if ( !str_devid ) {
			str_devid = new Date().getTime()+str_pushId;
			$.cookie('YDCWSDEVID', $.md5(str_devid));
		}
		
		if ( b_isHttps ) {
			str_bpushUrl = 'https'+str_bpushUrl;
		} else {
			str_bpushUrl = 'http'+str_bpushUrl;
		}
		str_pushUrl = 'packet_type=C1&from=0&push_id='+str_pushId+'&psd='+str_pushKey+'&devid='+str_devid;
		
		socketCon = io.connect(str_bpushUrl, {'query': str_pushUrl, 'reconnect': false, 'force new connection': true});
		
		//侦听服务
		socketCon.on('api/resp', function(data) {	
			//console.log('firsr push log:  ',data,typeof(data));
		    //var obj_pushData = JSON.parse(data),
			var obj_pushData = data,
				str_packetType = '';//obj_pushData.packet_type;
			
			if ( typeof(obj_pushData) == 'string' ) {
				obj_pushData = JSON.parse(data);
			}
			str_packetType = obj_pushData.packet_type;
			if ( $.browser.webkit ) {
				console.log('push log:   ',obj_pushData.tid,str_packetType,obj_pushData);
			}
			switch (str_packetType) {
				case 'S3':
					//定位器组织结构变化
					fn_pushOrganiztionStatus(obj_pushData);
					break;
				case 'S4':
					//定位器在线/离线消息
					fn_pushTerminalLoginSt(obj_pushData);					
					break;
				case 'S5':
					//定位器告警
					fn_pushTerminalAlert(obj_pushData);
					break;
				case 'S6':
					//定位器基本状态
					fn_pushTerminalStatusUpdate(obj_pushData);
					break;
				case 'S7':
					//定位器基本资料
					fn_pushTerminalDataUpdate(obj_pushData);
					break;
				case 'S8':
					//开解锁回显
					fn_pushTerminal210AccMessageUpdate(obj_pushData);
					break;
			}
		});
		
		//侦听连接失败
		socketCon.on('error', function(event){
			//socketCon.disconnect();
			//if ( event != 'handshake unauthorized' ) {
				socketCon.disconnect();
			//}
			//setTimeout(function(e) {
			//	fn_reRequestPush();
			//}, 1000*10);
		});
		
		socketCon.on('disconnect', function(event){
			if ( $.browser.webkit ) {
				console.log('push  disconnect:   ',event);
			}
			//if ( confirm('网络连接已断开，是否重新连接?') ) {
				fn_reRequestPush();
			//}
		});
	}
	
	//重新请求push信息
	function fn_reRequestPush() {
		$.ajax({
			type : 'get',
			url : '/wspush',
			data: '',
			dataType : 'json',
			cache: false,
			contentType : 'application/json; charset=utf-8',
			success : function(data) {
				if ( data.status == 0) {
					var obj_pushData = data.wspush;
					
					$('#push_key').val(obj_pushData.key);
					$('#push_id').val(obj_pushData.id);
					
					dlf.fn_initPushServices();
				} else if ( data.status == 403 || data.status == 24 ) {
					window.location.replace('/');
				} else {
					setTimeout(function(e) {
						fn_reRequestPush();
					}, 1000*10);
				}
			},
			error : function(XMLHttpRequest) {
				//dlf.fn_serverError(XMLHttpRequest);
				setTimeout(function(e) {
					fn_reRequestPush();
				}, 1000*10);
				return;
			}
		});
	}
	//定位器组织结构变化
	function fn_pushOrganiztionStatus(obj_pushData) {
		dlf.fn_corpGetCarData();
		
		var obj_pushCallbackData = {'packet_type': 'C3', 'status': 0, 'msg': 'SUCCESS'};
		
		fn_pushCallback(obj_pushCallbackData);
	}
	//定位器在线/离线消息
	function fn_pushTerminalLoginSt(obj_pushData) {
		var obj_pushCallbackData = {'packet_type': 'C4', 'status': 0, 'msg': 'SUCCESS'},
			obj_pushRes = obj_pushData.res,
			obj_carDatas = $('.j_carList').data('carsData');
		
		if ( obj_carDatas ) {
			for ( var ia = 0; ia < obj_pushRes.length; ia++ ) {	
				var	obj_tempPushData = obj_pushRes[ia],
					str_tempPushTid = obj_tempPushData.tid,
					n_tempPushLoginSt = obj_tempPushData.login_status,
					obj_terminalData = obj_carDatas[str_tempPushTid],
					obj_selfMarker = obj_selfmarkers[str_tempPushTid],
					obj_leftTerminal = $('#leaf_'+str_tempPushTid);
				
				if ( obj_terminalData ) {
					if ( obj_terminalData.login != n_tempPushLoginSt ) {
						if ( n_tempPushLoginSt == 1 ) {
							n_onlineCnt++;
							n_offlineCnt--;
						} else {
							n_onlineCnt--;
							n_offlineCnt++;
						}
						obj_leftTerminal.attr('clogin', n_tempPushLoginSt);
						dlf.fn_updateTerminalLogin(obj_leftTerminal);
						if ( obj_selfMarker ) {
							var n_carTimestamp = obj_terminalData.timestamp,
								n_degree = obj_terminalData.degree,
								n_imgDegree = dlf.fn_processDegree(n_degree),	// 方向角处理
								n_speed = obj_terminalData.speed;

							// 设置marker的icon						
							dlf.fn_setMarkerTraceIcon(n_imgDegree, obj_terminalData.icon_type, n_tempPushLoginSt, obj_selfMarker, n_carTimestamp, n_speed);
						}
						obj_terminalData.login = n_tempPushLoginSt;
						obj_carDatas[str_tempPushTid] = obj_terminalData;
					}
				}
			}
			$('.j_carList').data('carsData', obj_carDatas);
			if ( n_onlineCnt < 0 ) { n_onlineCnt = 0; }
			if ( n_offlineCnt < 0 ) { n_offlineCnt = 0; }
			dlf.fn_updateTerminalCount();
		}
		
		fn_pushCallback(obj_pushCallbackData);
	}
	//定位器告警
	function fn_pushTerminalAlert(obj_pushData) {
		var obj_pushCallbackData = {'packet_type': 'C5', 'status': 0, 'msg': 'SUCCESS'},
			arr_alarm = [],
			obj_pushRes = obj_pushData.res,
			obj_carDatas = $('.j_carList').data('carsData');
		
		if ( obj_carDatas ) {
			for ( var ia = 0; ia < obj_pushRes.length; ia++ ) {	
				var	obj_tempPushData = obj_pushRes[ia],
					str_tempTid = obj_tempPushData.tid,
					obj_terminalData = obj_carDatas[str_tempTid],
					n_category = obj_tempPushData.category;
				
				if ( obj_terminalData ) {
					if ( obj_tempPushData.timestamp >= obj_terminalData.timestamp ) {
						if ( n_category != 1 ) {
							obj_tempPushData.owner_mobile = obj_terminalData.owner_mobile;
							arr_alarm.push(obj_tempPushData);
						}
						obj_terminalData.pbat = obj_tempPushData.pbat;
						obj_terminalData.timestamp = obj_tempPushData.timestamp;
						obj_terminalData.clongitude = obj_tempPushData.clongitude;
						obj_terminalData.clatitude = obj_tempPushData.clatitude;
						obj_terminalData.longitude = obj_tempPushData.longitude;
						obj_terminalData.latitude = obj_tempPushData.latitude;
						obj_terminalData.name = obj_tempPushData.name;
						obj_terminalData.speed = obj_tempPushData.speed;
						obj_terminalData.gsm = obj_tempPushData.gsm;
						obj_terminalData.gps = obj_tempPushData.gps;
						obj_terminalData.degree = obj_tempPushData.degree;
						obj_terminalData.locate_error = obj_tempPushData.locate_error;
						obj_terminalData.type = obj_tempPushData.type;
						obj_terminalData.alias = ''+obj_tempPushData.alias;	
					
						obj_carDatas[str_tempTid] = obj_terminalData;
						dlf.fn_updateInfoData(obj_terminalData);
						
						if ( dlf.fn_userType() ) {
							if ( $('#leafNode_'+str_tempTid).attr('class').search('jstree-checked') != -1 ) {
								dlf.fn_updateTerminalInfo(obj_terminalData);	// 更新车辆信息
							}
						}
					}					
				}
			}
			$('.j_carList').data('carsData', obj_carDatas);
			dlf.fn_updateAlarmList(arr_alarm);
		}
		
		fn_pushCallback(obj_pushCallbackData);
	}
	//定位器基本状态
	function fn_pushTerminalStatusUpdate(obj_pushData) {
		var obj_pushCallbackData = {'packet_type': 'C6', 'status': 0, 'msg': 'SUCCESS'},
			obj_pushRes = obj_pushData.res,
			obj_carDatas = $('.j_carList').data('carsData');
		
		if ( obj_carDatas ) {
			for ( var ia = 0; ia < obj_pushRes.length; ia++ ) {	
				var	obj_tempPushData = obj_pushRes[ia],
					str_tempTid = obj_tempPushData.tid,
					obj_carDatas = $('.j_carList').data('carsData'),
					obj_terminalData = obj_carDatas[str_tempTid],
					str_carcTid = dlf.fn_getCurrentTid();
				
				if ( obj_terminalData ) {
					obj_terminalData.gps = obj_tempPushData.gps;
					obj_terminalData.gsm = obj_tempPushData.gsm;
					obj_terminalData.pbat = obj_tempPushData.pbat;
					
					obj_carDatas[str_tempTid] = obj_terminalData;
					
					if ( str_carcTid == str_tempTid ) {
						dlf.fn_updateTerminalInfo(obj_terminalData);
					}
					
					$('.j_carList').data('carsData', obj_carDatas);
				}
			}
		}
		fn_pushCallback(obj_pushCallbackData);
	}
	//定位器基本资料
	function fn_pushTerminalDataUpdate(obj_pushData) {
		var obj_pushCallbackData = {'packet_type': 'C7', 'status': 0, 'msg': 'SUCCESS'},
			obj_pushRes = obj_pushData.res;
			obj_carDatas = $('.j_carList').data('carsData'),
			str_pushTempCurrentTid = dlf.fn_getCurrentTid();
		
		if ( obj_carDatas ) {
			for ( var ia = 0; ia < obj_pushRes.length; ia++ ) {	
				var	obj_tempPushData = obj_pushRes[ia],
					str_tempPushTid = obj_tempPushData.tid,
					str_tempPushAlias = obj_tempPushData.alias,
					n_tempPushIconType = obj_tempPushData.icon_type,
					str_tempPushOwnerMobile = obj_tempPushData.owner_mobile,					
					str_tempManual_status = obj_tempPushData.mannual_status,
					obj_terminalData = obj_carDatas[str_tempPushTid],
					obj_selfMarker = obj_selfmarkers[str_tempPushTid],					
					str_carcTid = dlf.fn_getCurrentTid();
			
				if ( obj_terminalData ) {
					var n_tempLoginSt = obj_terminalData.login,
						obj_leftTerminal = $('#leaf_'+str_tempPushTid);
					
					if ( str_tempPushAlias ) {
						obj_carDatas[str_tempPushTid].alias = str_tempPushAlias;
						obj_leftTerminal.attr('alias', dlf.fn_decode(str_tempPushAlias));
						obj_leftTerminal.html('<ins class="jstree-checkbox">&nbsp;</ins><ins class="jstree-icon">&nbsp;</ins>' + dlf.fn_encode(dlf.fn_dealAlias(str_tempPushAlias)))
					}
					if ( n_tempPushIconType ) {
						obj_carDatas[str_tempPushTid].icon_type = n_tempPushIconType;
						obj_leftTerminal.attr('icon_type', n_tempPushIconType);
					}
					if ( str_tempPushOwnerMobile ) {
						obj_carDatas[str_tempPushTid].owner_mobile = str_tempPushOwnerMobile;
					}
					if ( str_tempManual_status == 0 || str_tempManual_status ) {
						obj_carDatas[str_tempPushTid].mannual_status = str_tempManual_status;
						if ( str_carcTid == str_tempPushTid ) {
							dlf.fn_updateTerminalInfo(obj_carDatas[str_tempPushTid]);
						}
					}
					
					if ( obj_selfMarker ) {
						var obj_selfInfoWindow = obj_selfMarker.infoWindow;

						str_tempPushAlias = dlf.fn_encode(str_tempPushAlias);
						if ( obj_selfMarker.getLabel() ) {
							obj_selfMarker.getLabel().setContent(str_tempPushAlias);
						}		
						if ( str_pushTempCurrentTid == str_tempPushTid ) {
							if ( obj_selfInfoWindow ) {
								dlf.fn_createMapInfoWindow(obj_carDatas[str_tempPushTid], 'actiontrack');
								obj_selfMarker.openInfoWindow(obj_mapInfoWindow); // 显示吹出框
							}
						}
						var obj_carInfo = obj_carDatas[str_tempPushTid],
							n_carTimestamp = obj_carInfo.timestamp,
							n_clon = obj_carInfo.clongitude/NUMLNGLAT,
							n_clat = obj_carInfo.clatitude/NUMLNGLAT,
							n_degree = obj_carInfo.degree,
							n_imgDegree = dlf.fn_processDegree(n_degree),	// 方向角处理
							n_speed = obj_carInfo.speed,
							obj_tempPoint = new BMap.Point(n_clon, n_clat),
							str_actionTrack = dlf.fn_getActionTrackStatus(str_tempPushTid);
		
						obj_selfMarker.setPosition(obj_tempPoint);
						// 设置marker的icon						
						dlf.fn_setMarkerTraceIcon(n_imgDegree, n_tempPushIconType, n_tempLoginSt, obj_selfMarker, n_carTimestamp, n_speed);
						obj_selfmarkers[str_tempPushTid] = obj_selfMarker;
						
						if ( str_actionTrack == 'yes' ) {
							dlf.fn_updateOpenTrackStatusColor(str_tempPushTid);
						}
					}
					dlf.fn_updateTerminalLogin(obj_leftTerminal);
				}
			}
			$('.j_carList').data('carsData', obj_carDatas);
		}
		
		fn_pushCallback(obj_pushCallbackData);
	}
	
	//210开解锁消息回显
	function fn_pushTerminal210AccMessageUpdate(obj_pushData) {
		var obj_pushCallbackData = {'packet_type': 'C8', 'status': 0, 'msg': 'SUCCESS'},
			obj_pushRes = obj_pushData.res[0];
		
		if ( $('#accStatusWrapper').data(obj_pushRes.tid) ) {
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');
			dlf.fn_accCallback(obj_pushRes.acc_message, obj_pushRes.tid);
		}
		fn_pushCallback(obj_pushCallbackData);
	}
	
	//响应push
	function fn_pushCallback(obj_pushCallbackData) {
        //console.log("C:     ", obj_pushCallbackData)
		socketCon.emit('api/resp', obj_pushCallbackData);
	}
});
