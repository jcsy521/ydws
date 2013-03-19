/**
* 查询、统计操作方法(告警查询、截留旅客查询、动物截留查询、动物分类统计、黑名单管理、告警解除等操作)
* arr_dwRecordData: 查询结果集合
* n_dwRecordPageCnt: 分页的总页数
* n_dwRecordPageNum: 要查询的页码
* chart: 统计图对象
*/
var arr_dwRecordData = [],	// 后台查询到的报警记录数据
	n_dwRecordPageCnt = -1,	// 查询到数据的总页数,默认-1
	n_dwRecordPageNum = 0,	// 当前所在页数
	chart = null;
	
/**
* 初始化查询条件
*/
window.dlf.fn_initRecordSearch = function(str_who) {
	var obj_searchWrapper = $('#' + str_who + 'Wrapper');
	
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#cursor').hide();
	/* 初始化条件和数据 */
	$('.conditions input[type=text]').val('');
	$('#'+ str_who +'TableHeader').nextAll().remove();	// 清空tr数据
	$('#'+ str_who +'Page').hide();
	$('#'+ str_who +'CurrentPage').html('');
	$('#'+ str_who +'PageCount').html('');
	
	//dlf.fn_showOrHideSelect(str_who);	// IE6 select显示
	
	if ( str_who == 'event' || str_who == 'mileage' || str_who == 'statics' ) { // 告警查询 里程统计 告警统计 
		$('#POISearchWrapper').hide();  // 关闭周边查询
		dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
		dlf.fn_clearTrack();	// 初始化清除数据
		dlf.fn_clearMapComponent(); // 清除页面图形
		// 调整工具条和
		dlf.fn_setMapControl(10); /*调整相应的地图控件及服务对象*/
		fn_closeAllInfoWindow();	
		
		dlf.fn_initTimeControl(str_who); // 时间初始化方法

		$('#eventType option[value=-1]').attr('selected', true);	// 告警类型选项初始化
		dlf.fn_unLockScreen(); // 去除页面遮罩
	}
	dlf.fn_setSearchRecord(str_who); //  绑定查询的事件,查询,上下翻页
}

/**
* 初始化查询的分页、搜索按钮的事件方法
*/
window.dlf.fn_setSearchRecord = function(str_who) { 
	/*查询变量初始化*/
	arr_dwRecordData = [],	// 后台查询到的报警记录数据
	n_dwRecordPageCnt = -1,	// 查询到数据的总页数,默认-1
	n_dwRecordPageNum = 0;	// 当前所在页数
	
	
	/** 
	* 上一页按钮 下一页按钮
	*/
	var obj_prevPage = $('#'+ str_who +'PrevBtn'), 
		obj_nextPage = $('#'+ str_who +'NextBtn'), 
		obj_currentPage = $('#'+ str_who +'CurrentPage'),
		obj_search = $('#'+ str_who +'_searchBtn');
	/**
	* 上下页事件绑定
	*/
	obj_prevPage.unbind('click').bind('click', function() {
		if ( n_dwRecordPageNum <= 0) {
			return;
		}
		obj_currentPage.text(--n_dwRecordPageNum+1);
		dlf.fn_dwSearchData(str_who);
	});
	obj_nextPage.unbind('click').bind('click', function() {
		if ( n_dwRecordPageNum >= n_dwRecordPageCnt-1 ) {
			return;
		}
		obj_currentPage.text(++n_dwRecordPageNum+1);
		dlf.fn_dwSearchData(str_who);
	});
	obj_search.unbind('click').bind('click', function() {	// 告警记录查询事件
		n_dwRecordPageCnt = -1;
		n_dwRecordPageNum = 0;
		dlf.fn_dwSearchData(str_who);
	});
	
	dlf.fn_dialogPosition($('#' + str_who + 'Wrapper'));	// 设置dialog的位置并显示
}

/**
* 拼凑查询参数并查询数据
* str_who: 根据wrapper来拼凑查询参数
*/
window.dlf.fn_dwSearchData = function (str_who) {
	var obj_conditionData = {}, 
		str_getDataUrl = '', 
		arr_leafNodes = $('#corpTree .j_leafNode[class*=jstree-checked]'), 
		n_tidsNums = arr_leafNodes.length;
	
	$('#'+str_who+'TableHeader').nextAll().remove();	//清除页面数据
	switch (str_who) {
		case 'operator': //  操作员查询
			
			var str_mobile = $('#txt_oprMobile').val(),
				str_name = $('#txt_oprName').val(), 
				str_getDataUrl = OPERATOR_URL+'?name='+ str_name +'&mobile='+ str_mobile +'&pagecnt='+ n_dwRecordPageCnt +'&pagenum='+ n_dwRecordPageNum;
			
			if ( !MOBILEREG.test(str_mobile) ) {	// 手机号合法性验证
				dlf.fn_jNotifyMessage('您输入的手机号格式错误!', 'message', false);
			}
				
			break;
		case 'event': //  告警查询
			str_getDataUrl = EVENT_URL;
			dlf.fn_clearMapComponent(); // 清除页面图形
			
			var n_startTime = $('#eventStartTime').val(), // 用户选择时间
				n_endTime = $('#eventEndTime').val(), // 用户选择时间
				n_bgTime = dlf.fn_changeDateStringToNum(n_startTime), // 开始时间
				n_finishTime = dlf.fn_changeDateStringToNum(n_endTime), //结束时间
				n_category = $('#eventCategory').val(), 
				str_tids = '',
				str_userType = $('#user_type').val();
			
			obj_conditionData = {
								'start_time': n_bgTime, 
								'end_time': n_finishTime, 
								'pagenum': n_dwRecordPageNum, 
								'pagecnt': n_dwRecordPageCnt, 
								'category': n_category, 
								'tid': '',
								'tids': ''
							};
				
			if ( str_userType ==  USER_PERSON ) {
				obj_conditionData.tid = $('.j_currentCar').attr('tid');
			} else {
				if ( n_tidsNums <= 0 ) {
					dlf.fn_jNotifyMessage('请在左侧选择定位器。', 'message', false, 6000);
					return;	
				}
				obj_conditionData.tids = dlf.fn_searchCheckTerminal();
			}
			break;
		case 'mileage': // 里程统计
			str_getDataUrl = MILEAGE_URL;
			
			var n_startTime = $('#mileageStartTime').val(), // 用户选择时间
				n_endTime = $('#mileageEndTime').val(), // 用户选择时间
				n_bgTime = dlf.fn_changeDateStringToNum(n_startTime), // 开始时间
				n_finishTime = dlf.fn_changeDateStringToNum(n_endTime), //结束时间
				str_tids = '';
			
			obj_conditionData = {
							'start_time': n_bgTime, 
							'end_time': n_finishTime, 
							'pagenum': n_dwRecordPageNum, 
							'pagecnt': n_dwRecordPageCnt, 
							'tids': ''
						};	
			if ( n_tidsNums <= 0 ) {
				dlf.fn_jNotifyMessage('请在左侧选择定位器。', 'message', false, 6000);
				return;	
			}
			obj_conditionData.tids = dlf.fn_searchCheckTerminal();
			break;
		case 'statics': // 告警统计
			str_getDataUrl = STATICS_URL;
			
			var n_startTime = $('#staticsStartTime').val(), // 用户选择时间
				n_endTime = $('#staticsEndTime').val(), // 用户选择时间
				n_bgTime = dlf.fn_changeDateStringToNum(n_startTime), // 开始时间
				n_finishTime = dlf.fn_changeDateStringToNum(n_endTime); //结束时间
			
			if ( n_tidsNums <= 0 ) {
				dlf.fn_jNotifyMessage('请在左侧选择定位器。', 'message', false, 6000);
				return;	
			}
			obj_conditionData = {
						'start_time': n_bgTime, 
						'end_time': n_finishTime, 
						'pagenum': n_dwRecordPageNum, 
						'pagecnt': n_dwRecordPageCnt, 
						'tids': dlf.fn_searchCheckTerminal()
					};
			break;
	}			
	
	dlf.fn_jNotifyMessage('记录查询中' + WAITIMG, 'message', true);
	
	if ( str_who == 'operator' ) {
		$.get_(str_getDataUrl, '', function(data) {	
			dlf.fn_bindSearchRecord(str_who, data);
		},
		function(XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
	} else {
		$.post_(str_getDataUrl, JSON.stringify(obj_conditionData), function(data) {	
			dlf.fn_bindSearchRecord(str_who, data);
		},
		function(XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
	}
}
/*
* 绑定页面连接及操作的事件 
*/
window.dlf.fn_bindSearchRecord = function(str_who, obj_resdata) {
	var obj_prevPage = $('#'+ str_who +'PrevBtn'),
		obj_nextPage = $('#'+ str_who +'NextBtn'), 
		obj_pagination = $('#'+ str_who +'Page'), 
		obj_searchHeader = $('#'+str_who+'TableHeader');
		
	if ( obj_resdata.status == 0 ) {  // success
		var n_eventDataLen = 0,
			str_tbodyText = '';
			
		n_dwRecordPageCnt = obj_resdata.pagecnt;
		arr_dwRecordData = obj_resdata.res;
		n_eventDataLen = arr_dwRecordData.length; 	//记录数
		
		if ( n_eventDataLen > 0 ) {	// 如果查询到数据
			obj_pagination.show(); //显示分页
			if ( n_dwRecordPageCnt > 1 ) {	// 总页数大于1 
				if ( n_dwRecordPageNum > 0 && n_dwRecordPageNum < n_dwRecordPageCnt-1 ) {  //上下页都可用
					dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage0', 'prevPage1'));
					dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage0', 'nextPage1'));
				} else if ( n_dwRecordPageNum >= n_dwRecordPageCnt-1 ) {	//下一页不可用				
					dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage0', 'prevPage1'));
					dlf.fn_setItemMouseStatus(obj_nextPage, 'default', 'nextPage2');
				} else {	//上一页不可用
					dlf.fn_setItemMouseStatus(obj_prevPage, 'default', 'prevPage2');
					dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage0', 'nextPage1'));
				}
			} else {	//总页数小于1  上下页都不可用
				dlf.fn_setItemMouseStatus(obj_prevPage, 'default', 'prevPage2');
				dlf.fn_setItemMouseStatus(obj_nextPage, 'default', 'nextPage2');
			}
			
			if ( n_dwRecordPageNum == 0 ) {	// 只有在点击查询按钮时才重新显示总页数
				$('#'+ str_who +'PageCount').html(obj_resdata.pagecnt); //总页数
				$('#'+ str_who +'CurrentPage').html('1');	//当前页数
			}
			
			// 根据页面的不同生成相应的table表格
			dlf.fn_productTableContent(str_who, obj_resdata);
			
			/** 
			* 初始化奇偶行
			*/
			$('.dataTable tr').mouseover(function() {
				$(this).css('background-color', '#FFFACD');
			}).mouseout(function() {
				$(this).css('background-color', '');
			});
			//告警查询,添加点击显示上地图事件,并做数据存储
			if ( str_who == 'event' ) {
				/**
				* 用户点击位置进行地图显示
				*/
				$('.j_eventItem').click(function(event) {
					dlf.fn_clearMapComponent();
					/**
					* 根据行编号拿到数据，在地图上做标记显示
					*/
					var n_tempIndex = $(this).parent().parent().index()-1,
						obj_tempData = arr_dwRecordData[n_tempIndex];
					
						dlf.fn_addMarker(obj_tempData, 'eventSurround', 0, true); // 添加标记
						setTimeout (function () {
							var obj_centerPointer = dlf.fn_createMapPoint(obj_tempData.clongitude, obj_tempData.clatitude);
							dlf.fn_setOptionsByType('centerAndZoom', obj_centerPointer, 17);
						}, 100);
				});
			}			
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');
		} else {
			obj_pagination.hide(); //显示分页
			dlf.fn_jNotifyMessage('没有查询到记录。', 'message', false, 6000, 'dw');
		}
	} else if ( obj_resdata.status == 201 ) {	// 业务变更
		dlf.fn_showBusinessTip('event');
	} else {
		dlf.fn_jNotifyMessage(obj_resdata.message, 'message', false, 3000, 'dw');	
	}
}
/**
* 根据数据和页面不同生成相应的table域内容
*/
window.dlf.fn_productTableContent = function (str_who, obj_reaData) {
	var obj_searchData = obj_reaData.res, 
		n_searchLen = obj_searchData.length,
		obj_searchHeader = $('#'+str_who+'TableHeader'), 
		arr_graphic = obj_reaData.graphics,	// 统计图结果
		obj_counts = obj_reaData.counts,	// 每个种类的总数结果;
		str_tbodyText = '';
	
	for( var i = 0; i < n_searchLen; i++ ) {	
		var obj_tempData = obj_searchData[i], 
			str_id =  obj_tempData.id;
		
		switch (str_who) {
			case 'operator': // 操作员查询
				str_tbodyText+= '<tr id='+ str_id +'>';
				str_tbodyText+= '<td groupId ='+ obj_tempData.group_id +'>'+ obj_tempData.group_name +'</td>';	//组名
				str_tbodyText+= '<td>'+ obj_tempData.name +'</td>';	// 操作员姓名
				str_tbodyText+= '<td>'+ obj_tempData.mobile +'</td>';	//操作员手机号
				str_tbodyText+= '<td><a href="#" onclick=dlf.fn_editOperator('+ str_id +')>编辑</a></td>';	// 
				str_tbodyText+= '<td><a href="#" onclick=dlf.fn_deleteOperator('+ str_id +')>删除</a></td>';	
				str_tbodyText+= '</tr>';
				break;
			case 'event': // 告警查询
				var str_type = obj_tempData.category,	//类型
					n_lng = obj_tempData.clongitude/NUMLNGLAT,
					n_lat = obj_tempData.clatitude/NUMLNGLAT,
					str_location = obj_tempData.name, 
					str_tempAddress = str_location.length >= 30 ? str_location.substr(0,30) + '...':str_location,
					str_comment = obj_tempData.comment,	// 电量备注
					str_text = '';	//地址
					
					/**
					* 拼接table
					*/
					str_tbodyText+= '<tr>';
					str_tbodyText+= '<td>'+obj_tempData.alias+'</td>';
					str_tbodyText+= '<td>'+dlf.fn_changeNumToDateString(obj_tempData.timestamp)+'</td>';	// 告警时间
					str_tbodyText+= '<td>'+dlf.fn_eventText(str_type)+'</td>';	// 告警类型
					if ( n_lng == 0 || n_lat == 0 ) {	//无地址
						str_tbodyText+= '<td>无</td>';	
					} else {
						if ( str_location == '' || str_location == null ) {
							str_tbodyText+= '<td><a href="#"   onclick=dlf.fn_getAddressByLngLat('+n_lng+','+n_lat+','+ i +',"event") class="j_getPosition getPositionCss">获取位置</a></td>';
						} else {
							str_tbodyText+= '<td><label title="'+ str_location +'">'+str_tempAddress+'</label><a href="#" c_lon="'+n_lng+'" c_lat="'+n_lat+'" class="j_eventItem viewMap" >查看地图</a></td>';	//详细地址
						}
					}
					if ( str_comment == '' ) {
						str_tbodyText+= '<td>&nbsp;</td>';
					} else {
						str_tbodyText+= '<td>'+ str_comment +'</td>';
					}					
					str_tbodyText+= '</tr>';
				break;
			case 'mileage': // 里程 统计
				str_tbodyText+= '<tr>';
				str_tbodyText+= '<td>'+ obj_tempData.alias +'</td>';	// 车牌号
				str_tbodyText+= '<td>'+ obj_tempData.distance +'</td>';	//里程 
				str_tbodyText+= '</tr>';
				break;
			case 'statics': // 告警 统计
				var str_alias = obj_tempData.alias,	// 定位器手机号
					str_illegalmove = obj_tempData.illegalmove + '次',	// 非法移动
					str_sos = obj_tempData.sos + '次',	// sos
					str_illegashake =  obj_tempData.illegashake + '次', // 震动
					str_heartbeat_lost = obj_tempData.heartbeat_lost + '次',	// 心跳
					str_powerlow = obj_tempData.powerlow + '次';	// 低电
						//str_html = str_illegalmove + str_sos + str_illegashake + str_heartbeat_lost + str_powerlow;
					
					/**
					* 拼接table
					*/
					str_tbodyText+= '<tr>';
					str_tbodyText+= '<td>'+ str_alias +'</td>';	// 定位器
					str_tbodyText+= '<td>'+ str_illegalmove +'</td>';	// 告警详情
					/*str_tbodyText+= '<td>'+ str_sos +'</td>';	// 告警详情	暂不显示	*/
					str_tbodyText+= '<td>'+ str_illegashake +'</td>';	// 告警详情		
					str_tbodyText+= '<td>'+ str_heartbeat_lost +'</td>';	// 告警详情		
					str_tbodyText+= '<td>'+ str_powerlow +'</td>';	// 告警详情				
					str_tbodyText+= '</tr>';
				break;
		}
	}
	obj_searchHeader.after(str_tbodyText);
}

/**
*  时间控件初始化
*/
window.dlf.fn_initTimeControl = function(str_who) {
	
	var n_currentDate = new Date().getTime();
		str_nowDate = dlf.fn_changeNumToDateString(n_currentDate, 'ymd'), 
		str_inputStartTime = str_who+'StartTime', 
		str_inputEndTime = str_who+'EndTime',
		obj_stTime = $('#'+str_inputStartTime), 
		obj_endTime = $('#'+str_inputEndTime);
	
	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联
		WdatePicker({el: str_inputStartTime, dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, maxDate: '#F{$dp.$D(\''+str_inputEndTime+'\')}', qsEnabled: false,
		onpicked: function() {
			var obj_endDate = $dp.$D(str_inputEndTime), 
				str_endString = obj_endDate.y+'-'+obj_endDate.M+'-'+obj_endDate.d+' '+obj_endDate.H+':'+obj_endDate.m+':'+obj_endDate.s,
				str_endTime = dlf.fn_changeDateStringToNum(str_endString), 
				str_beginTime = dlf.fn_changeDateStringToNum($dp.cal.getDateStr());
			if ( str_endTime - str_beginTime > WEEKMILISECONDS) {
				obj_endTime.val(dlf.fn_changeNumToDateString(str_beginTime + WEEKMILISECONDS));
			}
		}});
	}).val(str_nowDate+' 00:00:00');
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: str_inputEndTime, dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, minDate: '#F{$dp.$D(\''+str_inputStartTime+'\')}', qsEnabled: false, 
			onpicked: function() {
				var obj_beginDate = $dp.$D(str_inputStartTime), 
					str_beginString = obj_beginDate.y+'-'+obj_beginDate.M+'-'+obj_beginDate.d+' '+obj_beginDate.H+':'+obj_beginDate.m+':'+obj_beginDate.s,
					str_beginTime = dlf.fn_changeDateStringToNum(str_beginString), 
					str_endTime = dlf.fn_changeDateStringToNum($dp.cal.getDateStr());
				if ( str_endTime - str_beginTime > WEEKMILISECONDS) {
					obj_stTime.val(dlf.fn_changeNumToDateString(str_endTime - WEEKMILISECONDS));
				}
			}
		});
	}).val(str_nowDate+' '+dlf.fn_changeNumToDateString(n_currentDate, 'sfm'));
	
}

/*
* 集团操作:查询当前选中的终端 
*/
window.dlf.fn_searchCheckTerminal = function() {
	// 获取当前选中的终端 
	var arr_leafNodes = $('#corpTree .j_leafNode[class*=jstree-checked]'), 
		n_tidsNums = arr_leafNodes.length, 
		str_tids = '';
		
	for (var i = 0; i < n_tidsNums; i++ ) {
		var obj_tempLeafNode = $($(arr_leafNodes[i]).children('a'));
		
		str_tids += obj_tempLeafNode.attr('tid')+',';
	}
	str_tids = str_tids.substr(0,str_tids.length - 1);
	return str_tids;
}
