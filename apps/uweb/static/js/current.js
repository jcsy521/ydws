/*
*实时定位相关操作方法
* 设防撤防操作
*/
(function () {
/**
* 实时定位初始化方法
*/
window.dlf.fn_currentQuery = function(str_flag) {
	var obj_pd = {'locate_flag': GPS_TYPE};	// 第一次post发起gps定位参数设置		
	
	dlf.fn_dialogPosition('realtime');	// 设置dialog的位置
	fn_currentRequest(obj_pd, str_flag);	// 发起定位请求
	$('#currentBtn').unbind('click').click(function() {	// 窗口关闭事件
		dlf.fn_closeDialog(); 
		dlf.fn_clearNavStatus('realtime');
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
		str_errorMsg = '定位失败，请尝试将定位器移至室外再次定位。'; //信号弱，暂时无法定位，请稍候重试。
	
	if ( n_locateFlag == GPS_TYPE ) {	// 上次请求是否是GPS定位，如果是则发起基站定位请求
		if ( n_cellstatus == 1 ) {
			/*obj_msg.html('GPS信号弱，切换到基站定位 ' + str_img);
			setTimeout(function () {
				fn_currentRequest(obj_pd);	// 上次是GPS定位，本次发起基站定位请求
			}, 3000);*/
			
			fn_currentRequest(obj_pd);	// 上次是GPS定位，本次发起基站定位请求
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
	dlf.fn_updateLastInfo();	// 动态更新定位器相关数据
}

/** 
* 向后台发起定位请求，并做相关处理
* 此方法：先向后台发送gps定位请求，如果gps定位失败则发起基站定位请求。
* obj_pd: 向后台发送的定位类型 GPS_TYPE or CELLID_TYPE
*/
function fn_currentRequest(obj_pd, str_flag) {
	var obj_cWrapper = $('#realtimeWrapper'),
		obj_msg = $('#currentMsg'), 
		str_errorMsg =  '定位失败，请尝试将定位器移至室外再次定位。',		// 信号弱，暂时无法定位，请稍候重试。'
		str_flagVal = obj_pd.locate_flag, 
		str_carCurrent = $('.currentCar').next().html(), // 当前车辆的别名
		str_img = '<img src="/static/images/blue-wait.gif" class="waitingImg" />',
		//str_msg = '车辆<b> '+ str_carCurrent +' </b>'
		str_msg = '车辆定位中，请等待',
		b_warpperStatus = obj_cWrapper.is(':visible'),
		str_tid = dlf.fn_getCurrentTid(),
		obj_tempCarsData = $('.j_carList').data('carsData');
	
	// 判断carsData中该终端是否有位置	
	if ( dlf.fn_isEmptyObj(obj_tempCarsData) ) {
		var obj_car = obj_tempCarsData[str_tid],
			n_lon = obj_car.longitude,
			n_lat = obj_car.latitude;	
		
		if ( n_lon == 0 || n_lat == 0 ) {	// 终端无上报位置点
			str_msg = '努力定位中，请稍后';
		}
	}
	obj_pd.tid = str_tid;
	if ( b_warpperStatus ) {	// 判断current dialog弹出框是否已经关闭，如果关闭:不进行任何操作
		/*if ( str_flagVal == CELLID_TYPE) {	// 根据定位类型设置提示信息
			str_msg += '基站定位进行中...';
		} else {
			str_msg += 'GPS定位进行中...';
		}*/
		obj_msg.html( str_msg + WAITIMG );
		dlf.fn_lockScreen(); // 添加页面遮罩
		dlf.fn_clearInterval(currentLastInfo);  // lastinfo停止计时
		$.post_(REALTIME_URL, JSON.stringify(obj_pd), function (postData) { // 发起post定位请求
			var p_warpperStatus = obj_cWrapper.is(':visible');
			
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
									$.get_(REALTIME_URL + '?tid=' + str_tid, '', function (getData) { // 通过get方法查询位置信息
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
				} else if ( n_callbackStatus == 301 || n_callbackStatus == 800 || n_callbackStatus == 801 )  {	// 301: gps信号弱 800: 定位器不在线 801: 定位器连接超时 发起基站定位
					fn_startCell(str_flagVal, n_cellstatus);
				} else { // 与后台连接失败  重新开启lastinfo
					fn_openLastinfo(str_errorMsg);	// postData.message
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
	dlf.fn_clearNavStatus('realtime');  // 移除导航操作中的样式
	dlf.fn_closeDialog();
	dlf.fn_updateLastInfo();	// 动态更新定位器相关数据
	mapObj.setCenter(dlf.fn_createMapPoint(obj_location.clongitude, obj_location.clatitude));	// 标记显示及中心点移动

	// realtime 修改存储数据
	var obj_car = $('.j_carList').data('carsData')[obj_location.tid];
	
	obj_car.name = obj_location.name;
	obj_car.degree = obj_location.degree;
	obj_car.timestamp = obj_location.timestamp;
	obj_car.longitude = obj_location.longitude;
	obj_car.clongitude = obj_location.clongitude;
	obj_car.latitude = obj_location.latitude;
	obj_car.clatitude = obj_location.clatitude;
	obj_car.type = obj_location.type;
	obj_car.speed = obj_location.speed;
	
	$('.j_carList').data('carsData')[obj_location.tid] = obj_car;
	
	dlf.fn_updateInfoData(obj_location, 'current');	// 对当前车的位置信息进行更新
	dlf.fn_updateTerminalInfo(obj_location, 'realtime');	// 对当前车的车辆信息进行更新
}

/**
* 设防撤防初始化
*/
window.dlf.fn_defendQuery = function(str_alias) {
	var n_defendStatus = 0,	// 设防撤防状态
		n_fob_status = 0,	// 挂件是否在附近 1: 在附近 0: 没在附近
		str_cTid = dlf.fn_getCurrentTid(),
		obj_defend = {'mannual_status': n_defendStatus, 'tids': str_cTid},	// 向后台传递设防撤防数据
		obj_dMsg = $('#defendMsg'),	// 设防撤防状态的提示信息容器
		n_keyNum = parseInt($('#carList .currentCar').eq(0).attr('keys_num')),	// 当前车辆的挂件数量
		obj_currentCar = $('.j_currentCar'),
		obj_defendBtn = $('#defendBtn'),	// 设防撤防的按钮
		str_tempAlias = '';
	
	if ( dlf.fn_userType() ) {
		str_tempAlias = str_alias || obj_currentCar.text().substr(2);
	} else {
		str_tempAlias = obj_currentCar.siblings(0).html();
	}
	obj_defendBtn.hide();
	dlf.fn_dialogPosition('defend');	// 设置dialog的位置
	dlf.fn_lockScreen();	//添加页面遮罩	
	$.get_(DEFEND_URL + '?tid=' + str_cTid, '', function(data) {
		if ( data.status == 0 ) {
			var str_defendStatus = data.mannual_status,  // 从后台获取到最新的设防撤防状态
				obj_wrapper = $('#defendWrapper'),	// 设防撤防容器
				str_html = '',	// 页面上显示的设防状态
				str_tip = '',	// 设防撤防中的提示信息
				str_dImg = '',	// 页面上显示的设防撤防图标
				obj_carData = $('.j_carList').data('carsData')[str_cTid];				
			
			n_fob_status = data.fob_status;
			obj_defendBtn.show();
			$('.currentCar').attr('fob_status', n_fob_status);	// 更新最新的 挂件状态  ：是否在附近
			if ( str_defendStatus == DEFEND_ON ) {
				n_defendStatus = DEFEND_OFF;
				str_tip = '您的定位器'+ str_tempAlias +'当前已设防。';
				dlf.fn_setItemMouseStatus(obj_defendBtn, 'pointer', new Array('cf', 'cf2'));	// 设置鼠标滑过设防或撤防按钮的样式
				str_html = '已设防';
				str_dImg = 'defend_status1.png';
			} else {
				n_defendStatus = DEFEND_ON;
				str_tip = '您的定位器'+ str_tempAlias +'当前未设防。';
				dlf.fn_setItemMouseStatus(obj_defendBtn, 'pointer', new Array('sf', 'sf2'));	// 设置鼠标滑过设防或撤防按钮的样式
				str_html = '未设防';
				str_dImg = 'defend_status0.png';
			}
			obj_defend['mannual_status'] = n_defendStatus;
			obj_defend['tids'] = str_cTid;
			obj_dMsg.html(str_tip);
			// 主页面设防状态
			$('#defendContent').html(str_html).data('defend', str_defendStatus);
			if ( obj_carData ) {
				obj_carData.mannual_status = str_defendStatus;	// 改变缓存中的设防撤防状态
			}
			$('.j_carList').data('carsData')[str_cTid] = obj_carData;
			$('#defendStatus').css('background-image', 'url("'+ dlf.fn_getImgUrl() + str_dImg +'")');	//.attr('title', str_html);
		} else if ( data.status == 201 ) {
			dlf.fn_showBusinessTip();
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
		}
	});
	
	$('#defendBtn').unbind('click').click(function() {	//设防撤防 业务保存	
		/**
		* 判断设防撤防时挂件状态和定位器在线状态
		* 1、挂件不在附近时如果defend_status 是0 jNoityMessage提示“挂件不在附近，确定要撤防吗？”
		*/
		fn_saveDefend(obj_defend);
	}); 
}

function fn_saveDefend(obj_defend, b_corp) {
	var n_defendStatus = obj_defend['mannual_status'],	// 设防撤防状态
		str_tip = '',
		str_wrapper = b_corp == true ? 'batchDefend' : 'defend';
		
	if ( n_defendStatus == DEFEND_OFF ) {
		str_tip = '撤防中';
	} else {
		str_tip = '设防中';
	}
	
	dlf.fn_jsonPost(DEFEND_URL, obj_defend, str_wrapper, str_tip);
}

/**
* 批量设防撤防
*/
window.dlf.fn_initBatchDefend = function(str_defend, obj_param) {
	dlf.fn_dialogPosition('batchDefend');	// 设置dialog的位置
	dlf.fn_echoData('batchDefendTable', obj_param, str_defend);
	var obj_defend = {},
		n_defendStatus = str_defend == '设防' ? DEFEND_ON : DEFEND_OFF;
	
	$('.j_batchDefend').removeClass('btn_delete').addClass('operationBtn').attr('disabled', false);	// 批量按钮变成灰色并且不可用
	$('.j_batchDefend').val('批量' + str_defend).unbind('click').bind('click', function() {
		obj_defend['mannual_status'] = n_defendStatus;
		obj_defend['tids'] = obj_param['tids'].join(',');
		
		fn_saveDefend(obj_defend, true);
	});
}
})();
