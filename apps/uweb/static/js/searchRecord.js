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
	arr_eventData = [],	// 后台查询到的报警记录数据
	chart = null;

/**
* 初始化查询条件
*/
window.dlf.fn_initRecordSearch = function(str_who) {
	var obj_currentWrapper = $('#' + str_who + 'Wrapper'),
		b_status  = obj_currentWrapper.is(':visible'),
		obj_tableHeader = $('#'+ str_who +'TableHeader');	// 查询结果表头
	
	if( str_who != 'eventSearch' ) {
		if ( b_status ) {	// 如果当前dialog打开又点击打开，不进行操作
			return;
		}
	}
	dlf.fn_clearNavStatus(str_who);
	dlf.fn_dialogPosition(str_who);	// 设置dialog的位置并显示
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#cursor').hide();
	/* 初始化条件和数据 */
	$('.conditions input[type=text]').val('');
	$('#'+ str_who +'TableHeader').nextAll().remove();	// 清空tr数据
	$('#'+ str_who +'Page').hide();
	$('#'+ str_who +'CurrentPage', '#'+ str_who +'PageCount', '.j_' + str_who + 'Foot').html('');
	$('#' + str_who + '_uploadBtn').hide();	// 隐藏下载按钮
	
	if ( str_who == 'eventSearch' ) { // 告警查询
		dlf.fn_ShowOrHideMiniMap(false);
		$('#eventSearchCategory').val(-1);
		obj_tableHeader.hide();
		dlf.fn_clearInterval(currentLastInfo); // 清除lastinfo计时器
		dlf.fn_clearTrack();	// 初始化清除数据
		dlf.fn_clearMapComponent(); // 清除页面图形
		
		dlf.fn_initTimeControl(str_who); // 时间初始化方法
		$('#eventType option[value=-1]').attr('selected', true);	// 告警类型选项初始化
		dlf.fn_unLockScreen(); // 去除页面遮罩
	} else if ( str_who == 'mileage' || str_who == 'onlineStatics' ) { // 里程统计 告警统计 
		obj_tableHeader.hide();
		$('#'+ str_who +'TableHeader').hide();
		dlf.fn_initTimeControl(str_who); // 时间初始化方法
		dlf.fn_unLockScreen(); // 去除页面遮罩
	} else if ( str_who == 'operator' ) {
		obj_tableHeader.hide();
		$('#txt_oprName, #txt_oprMobile').val('');	// 清空条件框
		$('#'+ str_who +'TableHeader').hide();
		dlf.fn_unLockScreen(); // 去除页面遮罩
	} else if ( str_who == 'singleEvent'|| str_who == 'singleMileage' ) {
		// 初始化条件
		var obj_searchYear = $('#'+ str_who + 'Year'),
			obj_searchMonth = $('#'+ str_who + 'Month'),
			obj_searchType = $('#' + str_who + 'Type'),
			obj_theadTH = $('.j_' + str_who + 'TH'),
			obj_content = $('.j_' + str_who + 'Content'),	// 内容区域
			obj_date = new Date(),	
			n_year = obj_date.getFullYear(),	// 当前年
			n_month = obj_date.getMonth() + 1,	// 当前月份
			str_alias = $('.j_currentCar').text().substr(2);
		
		$('.' + str_who + 'Table').hide();
		$('#'+ str_who +'Wrapper .j_chart').hide();	// 查看统计图链接隐藏
		$('.j_singleEventTitle, .j_singleMileageTitle').html(' - ' + str_alias);	// dialog的title显示当前定位器名称
		// obj_searchMonth.hide();	// 月份默认隐藏
		obj_searchYear.html(fn_generateSelectOption('year'));	// 填充年份
		obj_searchMonth.html(fn_generateSelectOption('month', obj_searchYear.val())).val(n_month).show();	// 填充月份
		obj_theadTH.html('日期');
		obj_content.css('height', '520px');
		obj_searchType.unbind('change').bind('change', function() {	// 当改变查询类型
			var str_val = $(this).val();
			
			if ( str_val == '1' ) {
				obj_searchMonth.hide();
			} else {
				obj_searchMonth.show();
			}
		}).val('2');
		
		obj_searchYear.unbind('change').bind('change', function() {	// 当改变年份的时候顺便改变月份
			var n_tempMonth = n_month;
			
			if ( n_year != $(this).val() ) {
				n_tempMonth = 1;
			}
			obj_searchMonth.html(fn_generateSelectOption('month', $(this).val())).val(n_tempMonth);
		});
	} else if ( str_who == 'operator' || str_who == 'passenger' ) {
		obj_tableHeader.hide();
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
	* 查询按钮    下载数据按钮
	*/
	var obj_prevPage = $('#'+ str_who +'PrevBtn'), 
		obj_nextPage = $('#'+ str_who +'NextBtn'), 
		obj_currentPage = $('#'+ str_who +'CurrentPage'),
		obj_search = $('#'+ str_who +'_searchBtn'),
		obj_download = $('#' + str_who + '_uploadBtn');
	/**
	* 上下页事件绑定 查询绑定  下载绑定
	*/
	obj_prevPage.unbind('click').bind('click', function() {
		if ( n_dwRecordPageNum <= 0) {
			return;
		}
		obj_currentPage.text(--n_dwRecordPageNum+1);
		dlf.fn_searchData(str_who);
	});
	obj_nextPage.unbind('click').bind('click', function() {
		if ( n_dwRecordPageNum >= n_dwRecordPageCnt-1 ) {
			return;
		}
		obj_currentPage.text(++n_dwRecordPageNum+1);
		dlf.fn_searchData(str_who);
	});
	obj_search.unbind('click').bind('click', function() {	// 查询数据事件
		n_dwRecordPageCnt = -1;
		n_dwRecordPageNum = 0;
		dlf.fn_searchData(str_who);
	});
	
	obj_download.unbind('click').bind('click', function() {	// 下载数据事件
		dlf.fn_downloadData(str_who);
	});
	
	if ( str_who == 'singleEvent' || str_who == 'singleMileage' ) {
		/**
		* 查看统计图 : 统计图事件
		*/
		$('#singleEventChart').dialog({
			autoOpen: false,
			width: 630,
			height: 480,
			resizable: false,	// 不可变大小
			modal: true,
			close: function() {
				$('.j_iframe').hide();
			}
		});
		$('#singleMileageChart').dialog({
			autoOpen: false,
			width: 630,
			height: 480,
			resizable: false,	// 不可变大小
			modal: true,
			close: function() {
				$('.j_iframe').hide();
			}
		});
		// 告警统计图
		$('#singleEventWrapper .j_chart').unbind('click').bind('click', function() {
			dlf.fn_showIframe('singleEvent');
			$('#singleEventChart').dialog('open');
		});
		// 里程统计图
		$('#singleMileageWrapper .j_chart').unbind('click').bind('click', function() {
			dlf.fn_showIframe('singleEvent');
			$('#singleMileageChart').dialog('open');
		});
	}
}

/**
* excel表格下载
* str_who: 下载对象
*/
window.dlf.fn_downloadData = function(str_who) {
	var str_downloadUrl = '';
	
	switch (str_who) {
		case 'mileage':
			str_downloadUrl = MILEAGEDOWNLOAD_URL;		
			break;
		case 'statics':
			str_downloadUrl = STATICSDOWNLOAD_URL;		
			break;
		case 'singleEvent':
			str_downloadUrl = SINGLESTATICSDOWNLOAD_URL;		
			break;
		case 'singleMileage':
			str_downloadUrl = SINGLEMILEAGEDOWNLOAD_URL;			
			break;
		case 'onlineStatics':
			str_downloadUrl = ONLINEDOWNLOAD_URL;
	}
	dlf.fn_jNotifyMessage('正在下载中' + WAITIMG, 'message', true);
	
	var str_hash = $('#' + str_who + 'Wrapper').data('hash');
	
	if ( str_hash != '' ) {
		dlf.fn_closeJNotifyMsg('#jNotifyMessage');	
		$('#' + str_who + '_uploadBtn').attr('href', str_downloadUrl + '?hash_=' + str_hash);
	} else {
		dlf.fn_jNotifyMessage('下载失败请稍后再试。', 'message', false, 3000);
		return;
	}
}

/**
* 拼凑查询参数并查询数据
* str_who: 根据wrapper来拼凑查询参数
*/
window.dlf.fn_searchData = function (str_who) {
	var obj_conditionData = {}, 
		str_getDataUrl = '', 
		arr_leafNodes = $('#corpTree .j_leafNode[class*=jstree-checked]'), 
		n_tidsNums = arr_leafNodes.length;
	
	switch (str_who) {
		case 'operator': //  操作员查询
			
			var str_mobile = $('#txt_oprMobile').val(),
				str_name = $('#txt_oprName').val(); 
			
			str_getDataUrl = OPERATOR_URL+'?name='+ str_name +'&mobile='+ str_mobile +'&pagecnt='+ n_dwRecordPageCnt +'&pagenum='+ n_dwRecordPageNum;
			
			if ( !MOBILEREG.test(str_mobile) ) {	// 手机号合法性验证
				dlf.fn_jNotifyMessage('您输入的手机号格式错误!', 'message', false);
			}
				
			break;
		case 'passenger': //  乘客查询
			
			var str_mobile = $('#txt_passenMobile').val(),
				str_name = $('#txt_passenName').val();
				
			str_getDataUrl = PASSENGER_URL+'?name='+ str_name +'&mobile='+ str_mobile +'&pagecnt='+ n_dwRecordPageCnt +'&pagenum='+ n_dwRecordPageNum;
			
			if ( !MOBILEREG.test(str_mobile) ) {	// 手机号合法性验证
				dlf.fn_jNotifyMessage('您输入的手机号格式错误!', 'message', false);
			}
				
			break;
		case 'infoPush': //  消息推送获取乘客信息
			str_getDataUrl = PUSHINFO_URL+'?name=&mobile=&pagecnt='+ n_dwRecordPageCnt +'&pagenum='+ n_dwRecordPageNum;
			break;
		case 'eventSearch': //  告警查询
			str_getDataUrl = EVENT_URL;
			dlf.fn_clearMapComponent(); // 清除页面图形
			// 设置地图父容器 小地图  地图title隐藏
			dlf.fn_ShowOrHideMiniMap(false);
			var n_startTime = $('#eventSearchStartTime').val(), // 用户选择时间
				n_endTime = $('#eventSearchEndTime').val(), // 用户选择时间
				n_bgTime = dlf.fn_changeDateStringToNum(n_startTime), // 开始时间
				n_finishTime = dlf.fn_changeDateStringToNum(n_endTime), //结束时间
				n_category = $('#eventSearchCategory').val(), 
				str_tids = '',
				str_userType = $('.j_body').attr('userType');
			
			obj_conditionData = {
								'start_time': n_bgTime, 
								'end_time': n_finishTime, 
								'pagenum': n_dwRecordPageNum, 
								'pagecnt': n_dwRecordPageCnt, 
								'category': n_category, 
								'tid': '',
								'tids': ''
							};
			
			if ( n_bgTime >= n_finishTime ) {	// 判断选择时间
				dlf.fn_jNotifyMessage('开始时间不能大于结束时间，请重新选择其他时间段。', 'message', false, 3000);
				return;
			}	
			if ( str_userType ==  USER_PERSON ) {
				obj_conditionData.tid = $('.j_currentCar').attr('tid');
			} else {
				if ( n_tidsNums <= 0 ) {
					dlf.fn_jNotifyMessage('请在左侧勾选定位器。', 'message', false, 6000);
					return;	
				}
				obj_conditionData.tids = dlf.fn_searchCheckTerminal();
			}
			break;
		case 'mileage': // 里程统计
			str_getDataUrl = MILEAGE_URL;
			
			var n_startTime = $('#mileageStartTime').val() + ' 00:00:00', // 用户选择时间
				n_endTime = $('#mileageEndTime').val() + ' 23:59:59', // 用户选择时间
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
			if ( n_bgTime >= n_finishTime ) {	// 判断选择时间
				dlf.fn_jNotifyMessage('开始时间不能大于结束时间，请重新选择时间段。', 'message', false, 3000);
				return;
			}
			if ( n_tidsNums <= 0 ) {
				dlf.fn_jNotifyMessage('请在左侧勾选定位器。', 'message', false, 6000);
				return;	
			}
			obj_conditionData.tids = dlf.fn_searchCheckTerminal();
			break;
		case 'onlineStatics': // 在线统计
			str_getDataUrl = ONLINE_URL;
			
			var n_startTime = $('#onlineStaticsStartTime').val() + ' 00:00:00', // 用户选择开始时间
				n_endTime = $('#onlineStaticsEndTime').val() + ' 23:59:59', // 用户选择结束时间
				n_bgTime = dlf.fn_changeDateStringToNum(n_startTime), 	// 开始时间
				n_finishTime = dlf.fn_changeDateStringToNum(n_endTime);	 //结束时间
			
			obj_conditionData = {
							'start_time': n_bgTime, 
							'end_time': n_finishTime, 
							'pagenum': n_dwRecordPageNum, 
							'pagecnt': n_dwRecordPageCnt
						};

			if ( n_bgTime >= n_finishTime ) {	// 判断选择时间
				dlf.fn_jNotifyMessage('开始时间不能大于结束时间，请重新选择时间段。', 'message', false, 3000);
				return;
			}
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
		case 'singleEvent': // 单个定位器的告警统计
			str_getDataUrl = SINGLESTATICS_URL;
			var n_type = parseInt($('#'+ str_who +'Type').val()), 
				str_year = $('#'+ str_who +'Year').val(),
				str_tid = $('.j_currentCar').attr('tid'),
				str_month = '';
			
			obj_conditionData = {'tid': str_tid, 'statistics_type': n_type, 'year': str_year, 'month': str_month, 'pagenum': n_dwRecordPageNum, 'pagecnt': n_dwRecordPageCnt};
			
			/*根据选择的时间类型做相应处理*/
			if ( n_type ==  2 ) { // 按月
				obj_conditionData.month = $('#'+ str_who +'Month').val();
			}
			break;
		case 'singleMileage': // 单个定位器的告警统计
			str_getDataUrl = SINGLEMILEAGE_URL;
			var n_type = parseInt($('#'+ str_who +'Type').val()), 
				str_year = $('#'+ str_who +'Year').val(),
				str_tid = $('.j_currentCar').attr('tid'),
				str_month = '';
			
			obj_conditionData = {'tid': str_tid, 'statistics_type': n_type, 'year': str_year, 'month': str_month, 'pagenum': n_dwRecordPageNum, 'pagecnt': n_dwRecordPageCnt};
			
			/*根据选择的时间类型做相应处理*/
			if ( n_type ==  2 ) { // 按月
				obj_conditionData.month = $('#'+ str_who +'Month').val();
			}
			break;
		case 'routeLine': // 线路管理查询
			str_getDataUrl = ROUTELINE_URL+'?pagecnt='+ n_dwRecordPageCnt +'&pagenum='+ n_dwRecordPageNum;
			break;
		case 'bindRegion': // 绑定围栏管理查询
		case 'bindBatchRegion': // 批量绑定围栏管理查询
		case 'region': // 围栏管理查询
			str_getDataUrl = REGION_URL;
			$('#regionTable').removeData();
			break;
	}
	
	dlf.fn_jNotifyMessage('记录查询中' + WAITIMG, 'message', true);
	
	if ( str_who == 'operator' || str_who == 'region' || str_who == 'bindRegion' || str_who == 'bindBatchRegion' || str_who == 'passenger' || str_who == 'infoPush' || str_who == 'routeLine' ) {
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
/**
* 绑定页面连接及操作的事件 
*/
window.dlf.fn_bindSearchRecord = function(str_who, obj_resdata) {
	var obj_prevPage = $('#'+ str_who +'PrevBtn'),	// 上一页按钮
		obj_nextPage = $('#'+ str_who +'NextBtn'), 	// 下一页按钮
		obj_pagination = $('#'+ str_who +'Page'), 	// 分页容器
		obj_searchHeader = $('#'+str_who+'TableHeader'),	// 数据表头
		obj_download = $('#' + str_who + '_uploadBtn'),	// 下载数据按钮
		arr_btnPrevArray = new Array('prevPage0', 'prevPage1'), // 上一页按钮样式
		arr_btnNextArray = new Array('nextPage0', 'nextPage1'), //下一页按钮样式
		str_btnPrevDefault = 'prevPage2', // 上一页按钮默认样式
		str_btnNextDefault = 'nextPage2', // 下一页按钮默认样式
		str_enableColor = '#4876FF',
		str_disableColor = '#8E9090',
		obj_infoPushEle = $('#infoPush_allCheckedPanel, #infoPushSave'),
		obj_infoPushTipsEle = $('.j_infoPushTips, #infoPushDisabledBtn');
			
	if ( obj_resdata.status == 0 ) {  // success
		var n_eventDataLen = 0,
			str_tbodyText = '';
							// 下载按钮显示
		$('#'+ str_who +'Wrapper .j_chart').css('display', 'inline-block'); // 显示查看统计图连接
		
		obj_searchHeader.nextAll().remove();	//清除页面数据
		$('.j_'+ str_who +'Foot').empty();	// 清空foot数据
		n_dwRecordPageCnt = obj_resdata.pagecnt;
		arr_dwRecordData = obj_resdata.res; 
		
		if ( str_who == 'eventSearch' ) {
			arr_dwRecordData = obj_resdata.events;
		} else if ( str_who == 'passenger' || str_who == 'infoPush' ) {
			arr_dwRecordData = obj_resdata.passengers;
		} else if ( str_who == 'routeLine' ) {
			arr_dwRecordData = obj_resdata.lines;
		} else if ( str_who == 'region' || str_who == 'bindRegion' || str_who == 'bindBatchRegion' ) {
			arr_dwRecordData = obj_resdata.regions;
		}
		
		n_eventDataLen = arr_dwRecordData.length; 	//记录数
		if ( n_eventDataLen > 0 ) {	// 如果查询到数据
			$('.' + str_who + 'Table').show();
			obj_infoPushEle.show();
			obj_infoPushTipsEle.hide();	// infoPush没有查询到乘客信息提示框隐藏
			obj_download.show();
			obj_pagination.show(); //显示分页
			if ( n_dwRecordPageCnt > 1 ) {	// 总页数大于1 
				if ( n_dwRecordPageNum > 0 && n_dwRecordPageNum < n_dwRecordPageCnt-1 ) {  //上下页都可用
					if ( str_who == 'infoPush' ) {
						
					} else {
						dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', arr_btnPrevArray);
						dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', arr_btnNextArray);
					}
				} else if ( n_dwRecordPageNum >= n_dwRecordPageCnt-1 ) {	//下一页不可用	
					if ( str_who == 'infoPush' ) {
						obj_prevPage.css('color', str_enableColor);
						obj_nextPage.css('color', str_disableColor);
					} else {
						dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', arr_btnPrevArray);
						dlf.fn_setItemMouseStatus(obj_nextPage, 'default', str_btnNextDefault);
					}
				} else {	//上一页不可用
					if ( str_who == 'infoPush' ) {
						obj_prevPage.css('color', str_disableColor);
						obj_nextPage.css('color', str_enableColor);
					} else {
						dlf.fn_setItemMouseStatus(obj_prevPage, 'default', str_btnPrevDefault);
						dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', arr_btnNextArray);
					}
				}
			} else {	//总页数小于1  上下页都不可用
				if ( str_who == 'infoPush' ) {
						obj_prevPage.css('color', str_disableColor);
						obj_nextPage.css('color', str_disableColor);
				} else {
					dlf.fn_setItemMouseStatus(obj_prevPage, 'default', str_btnPrevDefault);
					dlf.fn_setItemMouseStatus(obj_nextPage, 'default', str_btnNextDefault);
				}
			}
			
			if ( n_dwRecordPageNum == 0 ) {	// 只有在点击查询按钮时才重新显示总页数
				$('#'+ str_who +'PageCount').html(obj_resdata.pagecnt); //总页数
				$('#'+ str_who +'CurrentPage').html('1');	//当前页数
			}
			dlf.fn_productTableContent(str_who, obj_resdata);	// 根据页面的不同生成相应的table表格
			dlf.fn_changeTableBackgroundColor();	// 数据行背景色改变
			
			//告警查询,添加点击显示上地图事件,并做数据存储
			if ( str_who == 'eventSearch' ) {
				dlf.fn_showMarkerOnEvent();
				// 关闭小地图
				$('.eventMapClose').unbind('click').bind('click', function() {
					dlf.fn_ShowOrHideMiniMap(false);
				});
			}
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');
			// 如果是围栏新增成功后,给用户提示绑定
			var obj_regionContent = $('#regionContent'),
				b_regionCreate = obj_regionContent.data('iscreate');
			if ( b_regionCreate ) {
				obj_regionContent.removeData('iscreate');
				dlf.fn_jNotifyMessage('创建成功，请绑定围栏。', 'message', false, 6000);
			}
		} else {
			obj_download.hide();
			obj_pagination.hide(); //显示分页
			if ( str_who == 'routeLine' ) {
				dlf.fn_closeJNotifyMsg('#jNotifyMessage');
				obj_searchHeader.after('<tr><td colspan="5" class="colorRed">没有查询到线路，请先创建。</td></tr>');
				return;
			} else if ( str_who == 'infoPush' ) {
				dlf.fn_closeJNotifyMsg('#jNotifyMessage');
				$('.j_infoPushChecks').html('');
				obj_infoPushEle.hide();
				obj_infoPushTipsEle.show();	// infoPush没有查询到乘客信息提示框隐藏
				return;
			} else {
				obj_searchHeader.hide();
			}
			if ( str_who == 'region' || str_who == 'bindRegion' || str_who == 'bindBatchRegion' ) {
				dlf.fn_closeJNotifyMsg('#jNotifyMessage');
			} else {
				dlf.fn_jNotifyMessage('没有查询到记录。', 'message', false, 6000);
			}
		}
	} else if ( obj_resdata.status == 201 ) {	// 业务变更
		dlf.fn_showBusinessTip('eventSearch');
	} else {
		dlf.fn_jNotifyMessage(obj_resdata.message, 'message', false, 3000);	
	}
}

String.prototype.len=function() {              
	return this.replace(/[^\x00-\xff]/g,"rr").length;          
}

/**
* 告警查询：用户点击位置进行地图显示
*/
window.dlf.fn_showMarkerOnEvent = function() {
	$('.j_eventItem').click(function(event) {
		dlf.fn_clearMapComponent();
		// 设置地图父容器 小地图显示 地图title显示
		dlf.fn_ShowOrHideMiniMap(true, event);
		dlf.fn_hideControl();
		// 根据行编号拿到数据，在地图上做标记显示
		var n_tempIndex = $(this).parent().parent().index()-1,
			obj_tempData = arr_dwRecordData[n_tempIndex];

			dlf.fn_addMarker(obj_tempData, 'eventSurround', 0, true, n_tempIndex); // 添加标记
			setTimeout (function () {
				// 为了正常显示暂时给告警的点加部分偏移进行显示:)
				var obj_centerPointer = dlf.fn_createMapPoint(obj_tempData.clongitude, obj_tempData.clatitude),
					n_category = obj_tempData.category,
					n_rid = obj_tempData.rid;
				
				// 如果是进出围栏告警则显示电子围栏
				if ( n_category == 7 || n_category == 8 ) {
					$.get_(GETREGIONDATA_URL +'?rid='+ n_rid, '', function (data) {  
						if ( data.status == 0 ) {
							var obj_circleData = data.region,
								obj_centerPoint = dlf.fn_createMapPoint(obj_circleData.longitude, obj_circleData.latitude);
							
							// dlf.fn_setOptionsByType('viewport', [obj_centerPoint, obj_centerPointer]);
							dlf.fn_displayCircle(obj_circleData);	// 调用地图显示圆形
							dlf.fn_setOptionsByType('centerAndZoom', obj_centerPointer, 15);
						} else if ( data.status == 201 ) {	// 业务变更
							dlf.fn_showBusinessTip();
						} else { // 查询状态不正确,错误提示
							dlf.fn_jNotifyMessage(data.message, 'message', false, 5000);
						}
					}, 
					function (XMLHttpRequest, textStatus, errorThrown) {
						dlf.fn_serverError(XMLHttpRequest);
					});
				} else {
					dlf.fn_setOptionsByType('centerAndZoom', obj_centerPointer, 17);
				}
			}, 100);
	});
}

/**
* 根据数据和页面不同生成相应的table域内容
*/
window.dlf.fn_productTableContent = function (str_who, obj_reaData) {
	var obj_searchData = obj_reaData.res;
	
	if ( str_who == 'eventSearch' ) {
		obj_searchData = obj_reaData.events;
	} else if ( str_who == 'passenger' || str_who == 'infoPush') {
		obj_searchData = obj_reaData.passengers;
	} else if ( str_who == 'routeLine' ) {
		obj_searchData = obj_reaData.lines;
	} else if ( str_who == 'region' || str_who == 'bindRegion' || str_who == 'bindBatchRegion' ) {
		obj_searchData = obj_reaData.regions;
		$('#regionTable').data({'regions': obj_searchData, 'regionnum': obj_searchData.length}); //围栏存储数据以便显示详细信息
	}

	arr_eventData = obj_searchData;
		
	var n_searchLen = obj_searchData.length,
		obj_searchHeader = $('#'+str_who+'TableHeader'), 
		arr_graphic = obj_reaData.graphics,	// 统计图结果
		obj_counts = obj_reaData.counts,	// 每个种类的总数结果;
		n_pagecnt = obj_reaData.pagecnt,	
		str_tbodyText = '',
		obj_tableHeader = $('#'+ str_who +'TableHeader'),	// 查询结果表头
		str_tfoot = '<tr><td>总计：</td>',
		str_hash = obj_reaData.hash_;	// 下载用的参数
	
	for( var i = 0; i < n_searchLen; i++ ) {	
		var obj_tempData = obj_searchData[i], 
			str_id =  obj_tempData.id;
		
		switch (str_who) {
			case 'operator': // 操作员查询
				obj_tableHeader.show();
				str_tbodyText+= '<tr id='+ str_id +'>';
				str_tbodyText+= '<td groupId ='+ obj_tempData.group_id +'>'+ obj_tempData.group_name +'</td>';	//组名
				str_tbodyText+= '<td>'+ obj_tempData.name +'</td>';	// 操作员姓名
				str_tbodyText+= '<td>'+ obj_tempData.mobile +'</td>';	//操作员手机号
				str_tbodyText+= '<td>'+ obj_tempData.address +'</td>';	// 操作员地址
				str_tbodyText+= '<td>'+ obj_tempData.email +'</td>';	//操作员email
				str_tbodyText+= '<td><a href="#" onclick=dlf.fn_editOperator('+ str_id +')>编辑</a></td>';	// 
				str_tbodyText+= '<td><a href="#" onclick=dlf.fn_deleteOperator('+ str_id +')>删除</a></td>';	
				str_tbodyText+= '</tr>';
				break;
			case 'passenger': // 乘客查询
				obj_tableHeader.show();
				str_tbodyText+= '<tr id='+ str_id +'>';
				str_tbodyText+= '<td>'+ obj_tempData.name +'</td>';	// 操作员姓名
				str_tbodyText+= '<td>'+ obj_tempData.mobile +'</td>';	//操作员手机号
				str_tbodyText+= '<td><a href="#" onclick=dlf.fn_editPassenger('+ str_id +')>编辑</a></td>';	// 
				str_tbodyText+= '<td><a href="#" onclick=dlf.fn_deletePassenger('+ str_id +')>删除</a></td>';	
				str_tbodyText+= '</tr>';
				break;
			case 'infoPush': // 消息推送
				var str_tempPid = obj_tempData.pid, 
					str_tempId = obj_tempData.id,
					str_pName = obj_tempData.name, 
					str_mobile =  obj_tempData.mobile,
					str_newPName = str_pName,
					str_checkText = '',
					b_checked = obj_infoPushChecks[str_tempId],
					n_pNameLen = str_newPName.lenth,
					str_grayClass = '',
					str_checkboxId = 'ck_' + str_tempPid,
					b_allChecked = $('#infoPush_allChecked').attr('checked');
				
				//todo中文和英文的长度验证及截取
				if ( n_pNameLen > 10 ) {
					str_newPName = str_pName.substr(0, 10) + '...';
				}
				// if ( str_tempPid == '' ) { // 是否有PID,是否已绑定手机
					// str_checkText = '<label class="passengerUnBind">(未绑定)</label>';
					// str_grayClass = 'gray';
				// } else {
					if ( b_checked || b_allChecked) {
						str_checkText = '<input type="checkbox" id="'+ str_checkboxId +'" checked="checked" name="infoPush_check" value="'+ str_tempPid +'" userid="'+ str_tempId +'" usermobile="' + str_mobile +'" />';
						obj_infoPushChecks[str_tempId] = str_tempPid || ''; //如果没有pid则设置为空
						obj_infoPushMobiles[str_tempId] = str_mobile || '';
					} else {
						str_checkText = '<input type="checkbox" id="'+ str_checkboxId +'" name="infoPush_check" value="'+ str_tempPid +'" userid="'+ str_tempId +'" usermobile="' + str_mobile +'" />';
					}
				//}
				str_tbodyText += '<label class="infoPushCheckPanel '+ str_grayClass +'" for="'+ str_checkboxId +'" title="'+ str_pName +'">'+ str_checkText + str_newPName +'</label>';
				break;
			case 'eventSearch': // 告警查询
				obj_tableHeader.show();
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
							str_tbodyText+= '<td><a href="#" onclick="dlf.fn_getAddressByLngLat(\''+n_lng+'\',\''+n_lat+'\',\'\',\'event\','+i+')" class="j_getPosition getPositionCss">获取位置</a></td>';
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
				obj_tableHeader.show();
				str_tbodyText+= '<tr>';
				str_tbodyText+= '<td>'+ obj_tempData.alias +'</td>';	// 车牌号
				str_tbodyText+= '<td>'+ obj_tempData.distance +'</td>';	//里程 
				str_tbodyText+= '</tr>';
				break;
			case 'onlineStatics':	// 在线统计
				$('#'+ str_who +'TableHeader').show();
				str_tbodyText+= '<tr>';
				str_tbodyText+= '<td>'+ dlf.fn_changeNumToDateString(obj_tempData.time*1000, 'ymd') +'</td>';	// 开通时间
				str_tbodyText+= '<td>'+ obj_tempData.online_num +'</td>';	// 在线数
				str_tbodyText+= '<td>'+ obj_tempData.offline_num +'</td>';	// 离线数
				str_tbodyText+= '<td>'+ obj_tempData.total_num +'</td>';	// 在线数
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
			case 'routeLine': // 线路管理
				var str_lineId = obj_tempData.line_id,
					arr_stations = obj_tempData.stations,
					n_stationNum = arr_stations ? arr_stations.length : 0;
			
				str_tbodyText+= '<tr id='+ str_lineId +'>';
				str_tbodyText+= '<td>'+ (i+1) +'</td>';	// 线路序号
				str_tbodyText+= '<td>'+ obj_tempData.line_name +'</td>';	// 线路名称
				str_tbodyText+= '<td>'+ n_stationNum +'</td>';	// 站点数量
				str_tbodyText+= '<td><a href="#" onclick=dlf.fn_detailRouteLine('+ str_lineId +')>查看详细</a></td>';	// 
				str_tbodyText+= '<td><a href="#" onclick=dlf.fn_deleteRouteLine('+ str_lineId +')>删除</a></td>';	
				str_tbodyText+= '</tr>';
				
				obj_routeLines[str_lineId] = obj_tempData; // 存储线信息以信显示线路详情
				break;
			case 'region': // 电子围栏
				//todo
				var str_regionId = obj_tempData.region_id,
					arr_regionName = obj_tempData.region_name;
			
				str_tbodyText+= '<tr id='+ str_regionId +'>';
				str_tbodyText+= '<td>'+ (i+1) +'</td>';	// 围栏序列
				str_tbodyText+= '<td>'+ arr_regionName +'</td>';	// 围栏名称
				str_tbodyText+= '<td><a href="#" onclick=dlf.fn_detailRegion('+ i +')>查看详情</a></td>';	// 
				str_tbodyText+= '<td><a href="#" onclick=dlf.fn_deleteRegion('+ str_regionId +')>删除</a></td>';	
				str_tbodyText+= '</tr>';
				
				break;
			case 'bindRegion': // 电子围栏绑定
			case 'bindBatchRegion': // 电子围栏批量绑定
				var str_regionId = obj_tempData.region_id,
					arr_regionName = obj_tempData.region_name,
					str_checkboxId = str_who+'Ck_' + str_regionId;
				
				str_tbodyText+= '<tr id='+ str_regionId +'>';
				str_tbodyText+= '<td>'+'<input type="checkbox" id="'+ str_checkboxId +'" name="'+ str_who +'_check" value="'+ str_regionId +'" /></td>';	// 围栏选择
				str_tbodyText+= '<td>'+ (i+1) +'</td>';	// 围栏序列
				str_tbodyText+= '<td>'+ arr_regionName +'</td>';	// 围栏名称
				str_tbodyText+= '<td><a href="#" onclick=dlf.fn_detailRegion('+ i +')>查看详情</a></td>';
				str_tbodyText+= '</tr>';
				
				break;
		}
	}
	obj_searchHeader.after(str_tbodyText);
	
	if ( str_who == 'singleMileage' || str_who == 'singleEvent' ) {
		var obj_tfoot = $('.j_'+ str_who +'Foot'),
			obj_theadTH = $('.j_' + str_who + 'TH'),	// 表头时间TH
			n_type = parseInt($('#'+ str_who +'Type').val()),
			obj_content = $('.j_' + str_who + 'Content'),	// 内容区域
			obj_month = $('#'+ str_who +'Month'),
			b_month = obj_month.is(':hidden'),
			str_alias = $('.j_currentCar').text().substr(2),	// 当前定位器名称
			obj_chart = {'name': str_alias, 'data': arr_graphic}, 
			arr_categories = [],
			str_unit = '次',
			str_container = 'singleEventChart',
			str_th = '日期',
			b_isLastPage = n_dwRecordPageNum != n_pagecnt-1,
			arr_series = [];	// 统计数据
				
		if ( str_who == 'singleEvent' ) {	// 单个定位器告警统计		
			for(var i = 0; i < n_searchLen; i++) {
				var obj_data = obj_searchData[i],
					str_name = obj_data.name,	// 如果是年报：2个月份、季报：四个季度、月报：30天
					obj_events = obj_data.events;	// 动物种类及数量
				
				str_tbodyText += '<tr><td>'+ str_name +'</td>';
				str_tbodyText+= '<td>'+ obj_events.illegalmove +'</td>';	// 
				str_tbodyText+= '<td>'+ obj_events.illegashake +'</td>';	//	
				str_tbodyText+= '<td>'+ obj_events.heartbeat_lost +'</td>';	// 
				str_tbodyText+= '<td>'+ obj_events.powerlow +'</td>';	// 			
				str_tbodyText+= '</tr>';
			}
		} else if ( str_who == 'singleMileage' ) {	// 单个定位器的里程统计
			for(var i = 0; i < n_searchLen; i++) {
				var obj_data = obj_searchData[i],
					str_name = obj_data.name,	// 如果是年报：2个月份、季报：四个季度、月报：30天
					n_mileage = obj_data.mileage;
				
				str_tbodyText += '<tr><td>'+ str_name +'</td>';
				str_tbodyText+= '<td>'+ n_mileage +'</td>';	// 里程数
				str_tbodyText+= '</tr>';
			}
			str_unit = '公里';
			str_container = 'singleMileageChart';
		}
		obj_searchHeader.after(str_tbodyText);	// 填充数据
		
		if ( !b_month && b_isLastPage ) {	// 如果是月报 &查询的是第一页  或者是 //todo : ) || ( str_who == 'onlineStatics' && n_pagecnt <= 1 && b_isLastPage ) 在线统计的foot						
			obj_tfoot.empty();
		} else {
			for ( var j = 0; j < obj_counts.length; j++ ) {
				str_tfoot += '<td>'+ obj_counts[j] + '</td>';
			}
			str_tfoot += '</tr>';
			obj_tfoot.empty().append(str_tfoot);
		}
		// 根据选择时间类型 设置统计图的x轴
		if ( n_type == 1 ) {
			arr_categories = ['1月', '2月', '3月', '4月', '5月', '6月', 
				'7月', '8月', '9月', '10月', '11月', '12月'];
			
			obj_content.css('height', '520px');
			str_th = '月份';
		} else if ( n_type == 2 ) {
			arr_categories = [];
			for ( var i = 0; i < arr_graphic.length; i++ ) {
				arr_categories.push( i+1 );
			}
			str_th = '日期';
			obj_content.css('height', '630px');
		}
		obj_theadTH.html(str_th);
		arr_series.push(obj_chart);
		fn_initChart(arr_series, arr_categories, str_container, str_unit, str_who);	// 初始化chart图
	} else if ( str_who == 'infoPush' ) {
		$('.j_infoPushChecks').html(str_tbodyText);
		
		// 绑定勾选框事件
		$('.j_infoPushChecks :checkbox[name="infoPush_check"]').unbind('click').click(function(event) {
			var str_isCheck = $(this).attr('checked'), 
				str_checkPid = $(this).val(),
				str_userid = $(this).attr('userid'), 
				str_mobile = $(this).attr('usermobile');
				
			if ( str_isCheck ) {
				obj_infoPushChecks[str_userid] = str_checkPid || ''; //如果没有pid则设置为空
				obj_infoPushMobiles[str_userid] = str_mobile || '';
			} else {
				obj_infoPushChecks[str_userid] = null;
				obj_infoPushMobiles[str_userid] = null;
				$('#infoPush_allChecked').removeAttr('checked');
			}
		});
	} else if ( str_who == 'bindRegion' ) { // 当前终端所绑定的围栏进行显示
		dlf.fn_getCurrentRegions();
	}
	$('#' + str_who + 'Wrapper').data('hash', str_hash);	// 存储hash值
}

/**
*  时间控件初始化
*/
window.dlf.fn_initTimeControl = function(str_who) {
	
	var n_currentDate = new Date().getTime();
		str_nowDate = dlf.fn_changeNumToDateString(n_currentDate, 'ymd'), 
		str_inputStartTime = str_who+'StartTime', 
		str_inputEndTime = str_who+'EndTime',
		str_tempBeginTime = str_nowDate+' 00:00:00',
		str_tempEndTime = str_nowDate+' '+dlf.fn_changeNumToDateString(n_currentDate, 'sfm'),
		str_timepickerFormat = 'yyyy-MM-dd HH:mm:ss',
		obj_stTime = $('#'+str_inputStartTime), 
		obj_endTime = $('#'+str_inputEndTime);
	
	if ( str_who == 'onlineStatics' || str_who == 'mileage' ) {
		str_tempEndTime = str_tempBeginTime = str_nowDate;
		str_timepickerFormat = 'yyyy-MM-dd';
	}
	
	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联 maxDate: '#F{$dp.$D(\''+str_inputEndTime+'\')}',minDate: '#F{$dp.$D(\''+str_inputStartTime+'\')}', // delete in 2013.04.10
		WdatePicker({el: str_inputStartTime, dateFmt: str_timepickerFormat, readOnly: true, isShowClear: false,  qsEnabled: false,
		onpicked: function() {
			if ( !dlf.fn_userType() ) {	// 如果是个人用户 有时间限制
				var obj_endDate = $dp.$D(str_inputEndTime), 
					str_endString = obj_endDate.y+'-'+obj_endDate.M+'-'+obj_endDate.d+' '+obj_endDate.H+':'+obj_endDate.m+':'+obj_endDate.s,
					str_endTime = dlf.fn_changeDateStringToNum(str_endString), 
					str_beginTime = dlf.fn_changeDateStringToNum($dp.cal.getDateStr());
				if ( str_endTime - str_beginTime > WEEKMILISECONDS) {
					obj_endTime.val(dlf.fn_changeNumToDateString(str_beginTime + WEEKMILISECONDS));
				}
			}
		}});
	}).val(str_tempBeginTime);
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: str_inputEndTime, dateFmt: str_timepickerFormat, readOnly: true, isShowClear: false, qsEnabled: false, 
			onpicked: function() {
				if ( !dlf.fn_userType() ) {	// 如果是个人用户 有时间限制
					var obj_beginDate = $dp.$D(str_inputStartTime), 
						str_beginString = obj_beginDate.y+'-'+obj_beginDate.M+'-'+obj_beginDate.d+' '+obj_beginDate.H+':'+obj_beginDate.m+':'+obj_beginDate.s,
						str_beginTime = dlf.fn_changeDateStringToNum(str_beginString), 
						str_endTime = dlf.fn_changeDateStringToNum($dp.cal.getDateStr());
					if ( str_endTime - str_beginTime > WEEKMILISECONDS) {
						obj_stTime.val(dlf.fn_changeNumToDateString(str_endTime - WEEKMILISECONDS));
					}
				}
			}
		});
	}).val(str_tempEndTime);
	
}

/**
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

/**
* 生成下拉列表项
* str_type: 要生成的类型 
*/
function fn_generateSelectOption(str_type, n_searchYear) {
	var str_options = '',
		obj_date = new Date(),
		n_year = obj_date.getFullYear(),	// 当前年
		n_currentMonth = obj_date.getMonth(),
		n_month = n_currentMonth + 1;		// 当前月份
	
	switch (str_type) {
		case 'year':
			for ( var n = n_year; n >= n_year-10; n-- ) {
				str_options += '<option value="'+ n +'">'+ n +'年</options>';
			}
			break;
		case 'month':
			if ( n_searchYear != n_year ) {
				n_month = 12;
			}
			for ( var m = 1; m <= n_month; m++ ) {
				str_options += '<option value="'+ m +'"> '+ m +'月</options>';
			}
			break;
	}
	return str_options;
}

/**
* 初始化 统计图
*/
function fn_initChart(arr_series, arr_categories, str_container, str_unit, str_who) {
	var str_title = $('#'+ str_who +'Year').val(),
		str_name = str_who == 'singleEvent' ? '告警' : '里程';
	
	if ( !$('#'+ str_who +'Month').is(':hidden') ) {
		str_title += '年'+ $('#'+ str_who +'Month').val() +'月份'+ str_name +'统计图' 
	} else {
		str_title += '年'+ str_name +'统计图' 
	}
	// 初始化统计图对象
	chart = new Highcharts.Chart({
				chart: {
					renderTo: str_container,
					defaultSeriesType: 'line'
				},
				title: {
					text: str_title,
					style: {
						margin: '10px 100px 0 0' // center it
					}
				},
				xAxis: {
					categories: arr_categories,
					title: {
						text: '时间'
					}
				},
				yAxis: {
					min: 0,                
					allowDecimals: false,
					title: {
						text: '总数('+ str_unit +')'
					},
					plotLines: [{
						value: 0,
						width: 1,
						color: '#808080'
					}]
				},
				tooltip: {
					formatter: function() {
							return '<b>'+ this.series.name +'</b><br/>'+
							this.x +': '+ this.y + str_unit;
					}
				},
				series: arr_series
			});
	$('svg text').last().remove();	// 移除 网址
}

window.dlf.fn_showIframe = function(str_wrapper) {
	// 设置iframe显示 
	var obj_wrapper = $('#' + str_wrapper + 'Wrapper'),
		n_top = 0,
		n_left = 0,
		obj_left = $(window),
		n_width = obj_left.width()- 20,
		n_height = obj_left.height() ;
		
	$('.j_iframe').css({'top': n_top, 'left': n_left, 'width': n_width, 'height': n_height}).show();
}

/**
* 调整地图的显示隐藏、位置、尺寸
* b_status: true: 告警查询、里程统计、操作员管理 false: 非告警查询
*/
window.dlf.fn_setMapPosition = function(b_status) {
	var obj_mapParentContainer = $('.mapContainer'),	// map外面的父元素
		obj_mapTitle = $('.mapDragTitle'),	// map容器外的title
		obj_map = $('#mapObj');
		
	if ( b_status ) {
		obj_map.hide();
		obj_mapParentContainer.draggable({handle: '.j_draggable', cursor:'move', containment: 'body', stop: function(event, ui) {	// 弹出的地图可以拖动
			if ( ui.position.top < 0 ) {
				$(this).css('top', 0);
			}
		}}).css('zIndex', 10000);
		
		//存储当前的中心点及比例尺数据,以便切换回来的时候显示 
		$('.j_body').data({'mapcenter': mapObj.getCenter(), 'mapsize': mapObj.getZoom()});
	} else {
		var n_windowHeight = $(window).height(),
			n_windowHeight = $.browser.version == '6.0' ? n_windowHeight <= 624 ? 624 : n_windowHeight : n_windowHeight,
			n_windowWidth = $(window).width(),
			n_windowWidth = $.browser.version == '6.0' ? n_windowWidth <= 1400 ? 1400 : n_windowWidth : n_windowWidth,
			n_mapHeight = n_windowHeight - 166,
			n_right = n_windowWidth - 249,
			obj_mapCenter = $('.j_body').data('mapcenter'),
			obj_mapSize = $('.j_body').data('mapsize');
		
		if ( $.browser.msie ) { // 根据浏览器不同调整页面部分元素大小 
			n_right = n_windowWidth - 249;
		}
		obj_map.css({'height': n_mapHeight, 'width': n_right, 'minHeight': 566, 'minWidth': 1151, 'zIndex': 0}).show();
		obj_mapParentContainer.removeAttr('style');
		obj_mapTitle.hide();	// 地图title隐藏
		dlf.fn_setMapControl(10); /*设置相应的地图控件及服务对象*/
		
		//设置地图默认属性
		if ( obj_mapCenter ) {
			setTimeout (function () {
				mapObj.setCenter(obj_mapCenter);
				mapObj.setZoom(obj_mapSize);
				$('.j_body').removeData('mapcenter mapsize');
			}, 300);
		}
	}
}
/*
* 告警查询关闭小地图
*/
window.dlf.fn_ShowOrHideMiniMap = function (b_isShow, event) {
	var obj_mapContainer = $('.mapContainer'), 
		obj_mapPanel = $('#mapObj'), 
		obj_mapConTitle = $('.mapDragTitle');
	
	if ( b_isShow ) {
		var n_top = event.clientY - 161;
		
		if ( n_top > 352) {
			n_top = event.clientY - 540;
		}
		// 设置地图父容器的样式
		obj_mapContainer.css({	
			'left': event.clientX - 200, 
			'top': n_top,
			'backgroundColor': '#FFFFFF',
			'border': '1px solid #BBBBBB',
			'height': '370px',
			'width': '370px',
			'padding': '10px',
			'zIndex': 10000
		});
		// 设置并显示小地图的样式
		obj_mapPanel.css({
			'width': 370,
			'height': 340,
			'minWidth': 370,
			'minHeight': 340,
			'zIndex': 10000
		}).show();
		// 地图title显示
		obj_mapConTitle.show();
	} else {
		obj_mapConTitle.hide();
		obj_mapPanel.hide();
		obj_mapContainer.removeAttr('style');
	}
}