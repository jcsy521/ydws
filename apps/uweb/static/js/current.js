/*
*实时定位相关操作方法
* 设防撤防操作
*/
(function () {
/**
* 实时定位初始化方法
*/
dlf.fn_currentQuery = function(str_flag) {
	var obj_pd = {'locate_flag': GPS_TYPE},
		n_cLogin = $('.j_currentCar').attr('clogin');	
	
	if ( n_cLogin == 0 ) {
		//dlf.fn_jNotifyMessage('定位器不在线！', 'message', false, 4000);
		//return;
	}
	
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
		str_msg = '定位器定位中，请等待',
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
	//使用完整数据
	dlf.fn_updateInfoData(obj_car, 'current');	// 对当前车的位置信息进行更新
	dlf.fn_updateTerminalInfo(obj_car, 'realtime');	// 对当前车的车辆信息进行更新
}

/**
* 设防撤防初始化
*/
dlf.fn_defendQuery = function(str_defendType, str_alias) {
	var str_cTid = dlf.fn_getCurrentTid(),
		obj_defend = {'mannual_status': 0, 'tids': str_cTid},	// 向后台传递设防撤防数据
		obj_currentCar = $('.j_currentCar'),
		str_tempAlias = '',
		str_msg = '',
		obj_carData = $('.j_carList').data('carsData')[str_cTid],
		n_defaultDefendSt = obj_carData.mannual_status,
		n_cLogin = $('.j_currentCar').attr('clogin');	
	
	if ( n_cLogin == 0 ) {
		//dlf.fn_jNotifyMessage('定位器不在线！', 'message', false, 4000);
		//return;
	}
	
	// 0撤防,1强,2智能,
	if ( str_defendType == 'smart' ) {
		obj_defend.mannual_status = 2;
		str_msg = '智能设防';
	} else if ( str_defendType == 'powerful' ) {
		obj_defend.mannual_status = 1;
		str_msg = '强力设防';
	} else if ( str_defendType == 'disarm' ) {
		obj_defend.mannual_status = 0;
		str_msg = '撤防';
	} 
	
	if ( obj_defend.mannual_status == n_defaultDefendSt ) {
		dlf.fn_jNotifyMessage('您已选择“'+str_msg+'”，请勿重复操作。', 'message', false, 4000);
		return;
	}
	
	if ( dlf.fn_userType() ) {
		obj_currentCar = $('.j_terminal[tid='+str_currentTid+']');
		
		str_tempAlias = str_alias || obj_currentCar.text().substr(2);
	} else {
		str_tempAlias = obj_currentCar.siblings(0).html();
	}
	str_tempAlias = dlf.fn_encode(str_tempAlias);
	
	//保存
	dlf.fn_jNotifyMessage(str_tempAlias+str_msg+'中' + WAITIMG, 'message', true);
	$('#userProfileManageList').hide();
	$.post_(DEFEND_URL, JSON.stringify(obj_defend), function (data) {
		if ( data.status == 0 ) {				
			var obj_carList = $('.j_carList'),
				obj_carsData = obj_carList.data('carsData'),
				obj_currentCar = $('.j_currentCar'),
				str_tid = obj_currentCar.attr('tid'),
				n_defendStatus = obj_defend.mannual_status,
				str_defendMsg = '',
				str_dImg = '';
				
			// 0撤防,1强,2智能,
			if ( n_defendStatus == '2' ) {
				str_defendMsg = '智能设防';
				str_dImg = 'defend_status1.png';
			} else if ( n_defendStatus == '1' ) {
				str_defendMsg = '强力设防';
				str_dImg = 'defend_status1.png';
			} else if ( n_defendStatus == '0' ) {
				str_defendMsg = '撤防';
				str_dImg = 'defend_status0.png';
			} 
			
			$('#defendContent').html(str_defendMsg).data('defend', n_defendStatus);	
			$('#defendStatus').css('background-image', 'url("' + dlf.fn_getImgUrl() + str_dImg + '")');	
		
			obj_carsData[str_tid].mannual_status = obj_defend.mannual_status;
			
			obj_carList.data('carsData', obj_carsData);
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip();
		}
		dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
	}, 
	function(XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}


/**
* 批量设防撤防
*/
dlf.fn_initBatchDefend = function(str_defend, obj_param) {
	dlf.fn_dialogPosition('batchDefend');	// 设置dialog的位置
	var obj_defend = {},
		n_defendStatus = str_defend,
		str_defnedMsg = '';
	
	if ( str_defend == '2' ) {
		str_defnedMsg = '智能设防';
	} else if ( str_defend == '1' ) {
		str_defnedMsg = '强力设防';
	} else if ( str_defend == '0' ) {
		str_defnedMsg = '撤防';
	} 
	dlf.fn_echoData('batchDefendTable', obj_param, str_defnedMsg);
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('.j_batchDefend').removeClass('btn_delete').addClass('operationBtn').attr('disabled', false);	// 批量按钮变成灰色并且不可用
	$('.j_batchDefend').val('批量' + str_defnedMsg).unbind('click').bind('click', function() {
		obj_defend['mannual_status'] = n_defendStatus;
		obj_defend['tids'] = obj_param['tids'].join(',');
		
		//保存
		dlf.fn_jNotifyMessage('批量' + str_defnedMsg+'中' + WAITIMG, 'message', true);
		
		$.post_(DEFEND_URL, JSON.stringify(obj_defend), function (data) {
			if ( data.status == 0 ) {				
				var arr_tids = obj_defend.tids.split(','),
					n_length = arr_tids.length,
					obj_carList = $('.j_carList'),
					obj_carsData = obj_carList.data('carsData'),
					obj_currentCar = $('.j_currentCar'),
					str_tid = obj_currentCar.attr('tid'),
					n_status = obj_defend.mannual_status,
					str_defendMsg = '',
					str_poDefendMsg = '',
					arr_datas = data.res;
				
				// 0撤防,1强,2智能,
				if ( n_status == '2' ) {
					str_defendMsg = '智能设防';
					str_poDefendMsg = '智能设防';
				} else if ( n_status == '1' ) {
					str_defendMsg = '强力设防';
					str_poDefendMsg = '强力设防';
				} else if ( n_status == '0' ) {
					str_defendMsg = '撤防';
					str_poDefendMsg = '撤防';
				} 
	
				if (  $('.j_currentCar').length == 0 ) {
					str_tid = str_currentTid;
					obj_currentCar = $('.j_terminal[tid='+ str_currentTid +']');
				}
				
				if ( n_length > 0 ) {	// 批量设防撤防
					for ( var i in arr_tids ) {
						var str_tempTid = arr_tids[i];
						
						obj_carsData[str_tempTid].mannual_status = n_status;
						if ( str_tid == str_tempTid ) {	// 如果批量中有当前定位器
							// todo 如果是集团用户 1、修改cardata里的数据  2、批量设防撤防如果有当前定位器要修改页面状态
							var str_defendStatus = parseInt(n_status),
								str_html = '',
								str_dImg = '',
								str_successMsg = '',
								n_defendStatus = 0,
								str_imgUrl = '';
							
							if ( str_defendStatus == '2' ) {
								str_html = '智能设防';
								str_dImg = 'defend_status1.png';
								n_defendStatus = 2;
							} else if ( str_defendStatus == '1' ) {
								str_html = '强力设防';
								str_dImg = 'defend_status1.png';
								n_defendStatus = 1;
							} else if ( str_defendStatus == '0' ) {
								str_html = '撤防';
								str_dImg = 'defend_status0.png';
								n_defendStatus = 0;
							}
							$('#defendContent').html(str_html).data('defend', n_defendStatus);
							$('#defendStatus').css('background-image', 'url("'+ dlf.fn_getImgUrl() + str_dImg + '")');	//.attr('title', str_html);
						}
					}
					for ( var x = 0; x < arr_datas.length; x++ ) {
						var obj_result = arr_datas[x],
							n_resultStatus = obj_result.status,
							str_resTid = obj_result.tid,
							obj_updateStatusTd = $('.batchDefendTable tbody td[tid='+ str_resTid +']'),
							str_msg = '',
							obj_updateDefendTd = obj_updateStatusTd.prev();
						
						if ( n_resultStatus == 0 ) {
							obj_updateStatusTd.html('操作成功').addClass('fileStatus4');
							obj_updateDefendTd.html(str_defendMsg);
						} else {
							obj_updateStatusTd.html('操作失败').addClass('fileStatus3');
							obj_updateDefendTd.html(str_poDefendMsg);
						}
					}			
					obj_carList.data('carsData', obj_carsData);
					$('.j_batchDefend').removeClass('operationBtn').addClass('btn_delete').attr('disabled', true);	// 批量按钮变成灰色并且不可用
				}
			} else if ( data.status == 201 ) {	// 业务变更
				dlf.fn_showBusinessTip();
			}
			dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
		}, 
		function(XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
	});
}
})();
