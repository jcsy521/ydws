/*
*实时定位相关操作方法
* 设防撤防操作
*/
(function () {
/**
* 实时定位初始化方法
*/
window.dlf.fn_currentQuery = function() {
	var obj_pd = {'locate_flag': GPS_TYPE};	// 第一次post发起gps定位参数设置
	
	dlf.fn_dialogPosition($('#currentWrapper'));	// 设置dialog的位置
	fn_currentRequest(obj_pd);	// 发起定位请求
	$('#currentBtn').unbind('click').click(function() {	// 窗口关闭事件
		dlf.fn_closeDialog(); 
	});
}

/** 
* 是否发起基站定位
* n_locateFlag: 定位类型GPS_TYPE or CELLID_TYPE
* n_cellstatus: 基站定位是否开启标志，1：开启基站定位 0：关闭基站定位
*/
function fn_startCell(n_locateFlag, n_cellstatus) {
	var obj_msg = $('#currentMsg'),
		obj_pd = {'locate_flag': CELLID_TYPE },	// 发起基站定位时向后台传送的数据
		str_img = '<img src="/static/images/blue-wait.gif" class="waitingImg" />',
		str_errorMsg = '无法获取车辆位置，请稍候重试！';
	
	if ( n_locateFlag == GPS_TYPE ) {	// 上次请求是否是GPS定位，如果是则发起基站定位请求
		if ( n_cellstatus == 1 ) {
			obj_msg.html('GPS信号弱，切换到基站定位 ' + str_img);
			setTimeout(function () {
				fn_currentRequest(obj_pd);	// 上次是GPS定位，本次发起基站定位请求
			}, 3000);
		} else {
			obj_msg.html(str_errorMsg);
		}										
	} else {
		fn_openLastinfo(str_errorMsg);	// 基站定位不成功 重新开启lastinfo
	}
}

/** 
* 定位失败 重新开启lastinfo
* str_msg: 定位失败时的错误消息
*/
function fn_openLastinfo(str_msg) {
	var obj_msg = $('#currentMsg');
	
	obj_msg.html(str_msg);
	dlf.fn_updateLastInfo();	// 动态更新终端相关数据
}

/** 
* 向后台发起定位请求，并做相关处理
* 此方法：先向后台发送gps定位请求，如果gps定位失败则发起基站定位请求。
* obj_pd: 向后台发送的定位类型 GPS_TYPE or CELLID_TYPE
*/
function fn_currentRequest(obj_pd) {
	var obj_cWrapper = $('#currentWrapper'),
		obj_msg = $('#currentMsg'), 
		str_errorMsg = '无法获取车辆位置，请稍候重试！',
		str_flagVal = obj_pd.locate_flag, 
		str_carCurrent = $('.currentCar').next().html(), // 当前车辆的别名
		str_img = '<img src="/static/images/blue-wait.gif" class="waitingImg" />',
		str_msg = '车辆<b> '+ str_carCurrent +' </b>'
		f_warpperStatus = !obj_cWrapper.is(':hidden');
	
	if ( f_warpperStatus ) {	// 判断current dialog弹出框是否已经关闭，如果关闭:不进行任何操作
		if ( str_flagVal == CELLID_TYPE) {	// 根据定位类型设置提示信息
			str_msg += '基站定位进行中 ';
		} else {
			str_msg += 'GPS定位进行中 ';
		}
		obj_msg.html( str_msg + str_img );
		dlf.fn_lockScreen(); // 添加页面遮罩
		dlf.fn_clearInterval(currentLastInfo);  // lastinfo停止计时
		$.post_(REALTIME_URL, JSON.stringify(obj_pd), function (postData) { // 发起post定位请求
			var p_warpperStatus = !obj_cWrapper.is(':hidden');
			
			if ( p_warpperStatus ) {	// 判断弹出框是否已经关闭，如果关闭:不进行任何操作
				var n_cellstatus = postData.cellid_status,	// 是否开启基站定位
					n_callbackStatus = postData.status;	// post请求的状态码
					
				if ( n_callbackStatus == 0  ) { // 	post请求成功
					if ( postData.location ) {	// post请求获取到位置信息
						fn_displayCurrentMarker(postData.location);
					} else {
							/** 
							* 每10秒发起一次get请求, 共发6次，如果查到结果则清除计时器
							* n_count: get请求的计数变量
							* c_countNum: get请求的最大请求次数
							*/
							var n_count = 0, c_countNum = CHECK_PERIOD / CHECK_INTERVAL;
							
							CURRENT_TIMMER = setInterval(function () { // 每10秒钟启动
								if ( n_count++ >= c_countNum ) {	// 达到get的最大请求次数
									dlf.fn_clearInterval(CURRENT_TIMMER);
									obj_msg.html(str_errorMsg);
									return;
								}
								var t_warpperStatus = !obj_cWrapper.is(':hidden');
								
								if ( t_warpperStatus ) { // 判断弹出框是否已经关闭，如果关闭:不进行任何操作
									$.get_(REALTIME_URL, '', function (getData) { // 通过get方法查询位置信息
										var g_warpperStatus = !obj_cWrapper.is(':hidden');
										
										if ( g_warpperStatus ) { // 判断弹出框是否已经关闭，如果关闭:不进行任何操作
											var n_getCallbackStatus = getData.status;
											
											if ( n_getCallbackStatus == 0 ) {
												if ( getData.location ) {	// 如果get拿到位置信息
													dlf.fn_clearInterval(CURRENT_TIMMER);
													fn_displayCurrentMarker(getData.location);
												} else {
													if ( n_count >= c_countNum ) {	// gps无法获取到位置信息时发起基站定位
														dlf.fn_clearInterval(CURRENT_TIMMER);
														fn_startCell(str_flagVal, n_cellstatus);
													}
												}
											} else if ( n_getCallbackStatus == 201 ) {	// 业务变更
												dlf.fn_showBusinessTip();
											} else { // 与后台连接失败 重新开启lastinfo
												dlf.fn_clearInterval(CURRENT_TIMMER);
												fn_openLastinfo(str_errorMsg);
											}
										}
									},
									function (XMLHttpRequest, textStatus, errorThrown) {
										dlf.fn_serverError(XMLHttpRequest);
									});
								}
							}, CHECK_INTERVAL);
					}
				} else if ( n_callbackStatus == 201 ) {	// 业务变更
					dlf.fn_showBusinessTip();
				} else if ( n_callbackStatus == 301 || n_callbackStatus == 800 || n_callbackStatus == 801 )  {	// 301: gps信号弱 800: 终端不在线 801: 终端连接超时 发起基站定位
					fn_startCell(str_flagVal, n_cellstatus);
				} else { // 与后台连接失败  重新开启lastinfo
					fn_openLastinfo(postData.message);
				}
			}
		}, 
		function(XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
	}
}

/**
* 实时定位获取到数据进行显示
* obj_location: 定位成功时的位置信息
*/
function fn_displayCurrentMarker(obj_location) {
	dlf.fn_closeDialog();
	dlf.fn_updateLastInfo();	// 动态更新终端相关数据
	mapObj.setCenter(new BMap.Point(obj_location.clongitude/NUMLNGLAT, obj_location.clatitude/NUMLNGLAT));	// 标记显示及中心点移动
	dlf.fn_updateInfoData(obj_location, 'current');	// 对当前车的位置信息进行更新
	dlf.fn_updateTerminalInfo(obj_location, 'realtime');	// 对当前车的车辆信息进行更新
}

/**
* 设防撤防初始化
*/
window.dlf.fn_defendQuery = function() {
	var n_defendStatus = 0,	// 设防撤防状态
		n_fob_status = 0,	// 挂件是否在附近 1: 在附近 0: 没在附近
		obj_defend = {};	// 向后台传递设防撤防数据
		
	$.get_(DEFEND_URL, '', function(data) {
		if ( data.status == 0 ) {
			var str_defendStatus = data.defend_status,  // 从后台获取到最新的设防撤防状态
				obj_dMsg = $('#defendMsg'),	// 设防撤防状态的提示信息容器
				obj_wrapper = $('#defendWrapper'),	// 设防撤防容器
				str_html = '',	// 页面上显示的设防状态
				str_tip = '',	// 设防撤防中的提示信息
				str_dImg = '',	// 页面上显示的设防撤防图标
				obj_defendBtn = $('#defendBtn');	// 设防撤防的按钮
			
			n_fob_status = data.fob_status;
			// todo 模拟挂件
			n_fob_status = 0;
			dlf.fn_lockScreen();	//添加页面遮罩
			dlf.fn_dialogPosition(obj_wrapper);	// 设置dialog的位置
			if ( str_defendStatus == DEFEND_ON ) {
				n_defendStatus = DEFEND_OFF;
				str_tip = '您的爱车保当前已设防。';
				dlf.fn_setItemMouseStatus(obj_defendBtn, 'pointer', new Array('cf', 'cf2'));	// 设置鼠标滑过设防或撤防按钮的样式
				str_html = '已设防';
				str_dImg = 'defend_status1.png';
			} else {
				if ( n_fob_status == FOB_ON ) {	// 如果挂件在附近 && 目前终端是撤防
					str_tip = '您的爱车保当前未设防,因检测挂件在附近，无法进行设防操作！';
					$('.j_defend').addClass('hide');	// 隐藏按钮和分割线
					$('#defendMsg').css('left', '0px');	// 设置提示信息的css
				} else {
					n_defendStatus = DEFEND_ON;
					str_tip = '您的爱车保当前未设防。';
					dlf.fn_setItemMouseStatus(obj_defendBtn, 'pointer', new Array('sf', 'sf2'));	// 设置鼠标滑过设防或撤防按钮的样式
				}
				str_html = '未设防';
				str_dImg = 'defend_status0.png';
			}
			obj_defend['defend_status'] = n_defendStatus;
			obj_dMsg.html(str_tip);
			// 主页面设防状态
			$('#defendContent').html(str_html).data('defend', str_defendStatus);	
			$('#defendStatus').css('background-image', 'url("'+ BASEIMGURL + str_dImg +'")').attr('title', str_html);
		} else if ( data.status == 201 ) {
			dlf.fn_showBusinessTip();
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
		}
	});
	
	$('#defendBtn').unbind('click').click(function() {	//设防撤防 业务保存	
		/**
		* 判断设防撤防时挂件状态和终端在线状态
		* 1、挂件不在附近时如果defend_status 是0 jNoityMessage提示“挂件不在附近，确定要撤防吗？”
		*/
		var n_defendStatus = obj_defend.defend_status,	// 设防撤防状态
			n_fobStatus = obj_defend.fob_status,	// 挂件是否在附近
			obj_defendMsg = $('#defendMsg'),			
			f_warpperStatus = !$('#wakeupWrapper').is(':hidden'),	// 容器是否显示
			obj_this = $(this);
				
		n_fobStatus = 0;	// todo 模拟 挂件不在附近
		if ( f_warpperStatus ) {
			dlf.fn_jNotifyMessage('追踪器正在唤醒中，请稍后再试！', 'message', false, 4000);
		} else {
			if ( n_fobStatus == FOB_OFF && n_defendStatus == DEFEND_OFF ) {	// 挂件不在附近,如果要撤防提示"确定要撤防吗？"
				$('#defendMsg').html('挂件不在附近，是否继续撤防？');
				dlf.fn_setItemMouseStatus(obj_this, 'pointer', new Array('jx', 'jx2')); // 设置鼠标滑过继续按钮的样式		
				obj_this.unbind('click').bind('click', function() {
					dlf.fn_terminalOnLine(DEFEND_URL, obj_defend, 'defend', '爱车保设防状态保存中...');
				});
			} else {
				dlf.fn_terminalOnLine(DEFEND_URL, obj_defend, 'defend', '爱车保设防状态保存中...');
			}
		}
	}); 
}

/**
* 判断终端是否在线
* 1、不在线(休眠中): 提示用户是否唤醒终端？
* 2、如果正在唤醒中，提示用户正在唤醒请稍后再试!
*/
window.dlf.fn_terminalOnLine = function(str_url, obj_data, str_operation, str_tips) {
	var n_login = parseInt($('#carList .currentCar').eq(0).attr('clogin')),	// 当前车辆的在线状态
		f_warpperStatus = !$('#wakeupWrapper').is(':hidden'),	// 容器是否显示
		obj_defendMsg = $('#defendMsg'),	// 提示框容器
		obj_defendBtn = $('#defendBtn'),	// 设防操作按钮
		str_msg = '';
	
	if ( n_login != LOGINST ) {	// 终端不在线
		// 判断"追踪器正在唤醒"提示是否显示
		if ( f_warpperStatus ) {	// 如果显示：正在唤醒中...请稍后
			str_msg = '追踪器正在唤醒中，请稍后再试！';
			dlf.fn_jNotifyMessage(str_msg, 'message', false, 5000);
		} else {
			str_msg = '追踪器不在线，是否唤醒追踪器？';
			if ( str_operation == 'defend' ) {
				obj_defendMsg.html(str_msg);
				dlf.fn_setItemMouseStatus(obj_defendBtn, 'pointer', new Array('hx', 'hx2'));	// 设置鼠标滑过唤醒的样式
				obj_defendBtn.unbind('click').bind('click', function() {
					fn_wakeupTerminal();
				});
			} else if ( str_operation == 'terminal' ) {
				if ( confirm(str_msg) ) {
					fn_wakeupTerminal();
				}
			}
		}
	} else {
		if ( str_url == '/terminal' ) {
			dlf.fn_jsonPut(str_url, obj_data, str_operation, str_tips);
		} else {
			dlf.fn_jsonPost(str_url, obj_data, str_operation, str_tips);
		}
	}
}

/**
* 唤醒追踪器
*/
function fn_wakeupTerminal() {
	var f_warpperStatus = !$('#wakeupWrapper').is(':hidden');	// 容器是否显示
	
	// 判断"追踪器正在唤醒"提示是否显示
	if ( f_warpperStatus ) {	// 如果显示：正在唤醒中...请稍后
		str_msg = '追踪器正在唤醒中，请稍后再试！';
		dlf.fn_jNotifyMessage(str_msg, 'message', false, 5000);
	} else {
		$.get_(WAKEUP_URL, '', function (data) {	// 唤醒追踪器请求
			if ( data.status == 0 ) {	// 成功下发唤醒短信，提示用户"追踪器正在唤醒中...."
				var str_wakeupMsg = '追踪器正在唤醒中' + WAITIMG,
					obj_wakeupMsg = $('#wakeupMsg'),
					obj_wakeupWrapper = $('#wakeupWrapper'),	// 追踪器唤醒提示容器
					obj_wakeupTimer = $('#wakeupTimer'),	// 追踪器提示框计时器容器
					n_timer = parseInt(obj_wakeupTimer.html()),
					wakeupInterval = null;
					n_left = ($(window).width()-300)/2;
				
				//dlf.fn_closeDialog();
				// 关闭jNotityMessage
				dlf.fn_closeJNotifyMsg('#jNotifyMessage'); 
				
				/**
				* 100秒 提示唤醒中 期间如果追踪器在线则隐藏
				*/
				obj_wakeupMsg.html(str_wakeupMsg);
				obj_wakeupWrapper.css('left', n_left + 'px').show();
				wakeupInterval = setInterval(function() {
					var n_login = parseInt($('#carList .currentCar').eq(0).attr('clogin'));	// 判断当前追踪器状态
					if ( n_timer < 100 ) {
						if ( n_login == LOGINST ) {	// 如果在线，关闭提示框、清计时器
							dlf.fn_clearInterval(wakeupInterval);
							obj_wakeupTimer.html('0');
							obj_wakeupWrapper.hide();
						}
					} else {
						dlf.fn_clearInterval(wakeupInterval);
						obj_wakeupTimer.html('0');
						obj_wakeupWrapper.hide();
						dlf.fn_jNotifyMessage('追踪器唤醒失败，请检查追踪器是否关机或欠费！', 'message', false, 5000);
					}
					n_timer++;
				}, 1000);
			} else if ( data.status == 201 ) {	// 业务变更
				dlf.fn_showBusinessTip();
			} else {
				dlf.fn_jNotifyMessage(data.message, 'message'); // 查询状态不正确,错误提示
			}
		});
	}
}

})();
