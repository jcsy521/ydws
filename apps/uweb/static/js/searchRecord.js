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
	dlf.fn_dialogPosition(str_who);	// 设置dialog的位置并显示
	dlf.fn_lockScreen(); // 添加页面遮罩
	$('#cursor').hide();
	/* 初始化条件和数据 */
	$('.conditions input[type=text]').val('');
	$('#'+ str_who +'TableHeader').nextAll().remove();	// 清空tr数据
	$('#'+ str_who +'Page').hide();
	$('#'+ str_who +'CurrentPage').html('');
	$('#'+ str_who +'PageCount').html('');
	$('.j_' + str_who + 'Foot').html('');	// 表格foot清空数据
	
	//dlf.fn_showOrHideSelect(str_who);	// IE6 select显示
	$('#' + str_who + '_uploadBtn').hide();	// 隐藏下载按钮
	if ( str_who == 'eventSearch' ) { // 告警查询 
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
	} else if ( str_who == 'mileage' || str_who == 'statics' ) { // 里程统计 告警统计 
		dlf.fn_initTimeControl(str_who); // 时间初始化方法
		dlf.fn_unLockScreen(); // 去除页面遮罩
	} else if ( str_who == 'singleEvent'|| str_who == 'singleMileage' ) {
		// 初始化条件
		var obj_searchYear = $('#'+ str_who + 'Year'),
			obj_searchMonth = $('#'+ str_who + 'Month'),
			obj_searchType = $('#' + str_who + 'Type'),
			obj_theadTH = $('.j_' + str_who + 'TH'),
			obj_content = $('.j_' + str_who + 'Content'),	// 内容区域
			str_alias = $('.j_currentCar').text().substr(2);
		
		$('#'+ str_who +'Wrapper .j_chart').hide();	// 查看统计图链接隐藏
		$('.j_singleEventTitle, .j_singleMileageTitle').html(' - ' + str_alias);	// dialog的title显示当前定位器名称
		// obj_searchMonth.hide();	// 月份默认隐藏
		obj_searchYear.html(fn_generateSelectOption('year'));	// 填充年份
		obj_searchMonth.html(fn_generateSelectOption('month', obj_searchYear.val()));	// 填充月份
		obj_theadTH.html('日期');
		obj_content.css('height', '400px');
		obj_searchType.unbind('change').bind('change', function() {	// 当改变查询类型
			var str_val = $(this).val();
			
			if ( str_val == '1' ) {
				obj_searchMonth.hide();
			} else {
				obj_searchMonth.show();
			}
		}).val('2');
		obj_searchYear.unbind('change').bind('change', function() {	// 当改变年份的时候顺便改变月份
			obj_searchMonth.html(fn_generateSelectOption('month', $(this).val()));
		});
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
				str_name = $('#txt_oprName').val(), 
				str_getDataUrl = OPERATOR_URL+'?name='+ str_name +'&mobile='+ str_mobile +'&pagecnt='+ n_dwRecordPageCnt +'&pagenum='+ n_dwRecordPageNum;
			
			if ( !MOBILEREG.test(str_mobile) ) {	// 手机号合法性验证
				dlf.fn_jNotifyMessage('您输入的手机号格式错误!', 'message', false);
			}
				
			break;
		case 'eventSearch': //  告警查询
			str_getDataUrl = EVENT_URL;
			dlf.fn_clearMapComponent(); // 清除页面图形
			
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
				dlf.fn_jNotifyMessage('请在左侧勾选定位器。', 'message', false, 6000);
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
/**
* 绑定页面连接及操作的事件 
*/
window.dlf.fn_bindSearchRecord = function(str_who, obj_resdata) {
	var obj_prevPage = $('#'+ str_who +'PrevBtn'),	// 上一页按钮
		obj_nextPage = $('#'+ str_who +'NextBtn'), 	// 下一页按钮
		obj_pagination = $('#'+ str_who +'Page'), 	// 分页容器
		obj_searchHeader = $('#'+str_who+'TableHeader'),	// 数据表头
		obj_download = $('#' + str_who + '_uploadBtn');	// 下载数据按钮
		
	if ( obj_resdata.status == 0 ) {  // success
		var n_eventDataLen = 0,
			str_tbodyText = '';
		
		obj_download.show();					// 下载按钮显示
		$('#'+ str_who +'Wrapper .j_chart').css('display', 'inline-block'); // 显示查看统计图连接
		
		obj_searchHeader.nextAll().remove();	//清除页面数据
		$('.j_'+ str_who +'Foot').empty();	// 清空foot数据
		n_dwRecordPageCnt = obj_resdata.pagecnt;
		arr_dwRecordData = str_who == 'eventSearch' ? obj_resdata.events : obj_resdata.res, 
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
			if ( str_who == 'eventSearch' ) {
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
							// 为了正常显示暂时给告警的点加部分偏移进行显示:)
							var obj_centerPointer = dlf.fn_createMapPoint(obj_tempData.clongitude-10000, obj_tempData.clatitude);
							
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
		dlf.fn_showBusinessTip('eventSearch');
	} else {
		dlf.fn_jNotifyMessage(obj_resdata.message, 'message', false, 3000, 'dw');	
	}
}

/**
* 根据数据和页面不同生成相应的table域内容
*/
window.dlf.fn_productTableContent = function (str_who, obj_reaData) {
	var obj_searchData = str_who == 'eventSearch' ? obj_reaData.events : obj_reaData.res, 
		n_searchLen = obj_searchData.length,
		obj_searchHeader = $('#'+str_who+'TableHeader'), 
		arr_graphic = obj_reaData.graphics,	// 统计图结果
		obj_counts = obj_reaData.counts,	// 每个种类的总数结果;
		str_tbodyText = '',
		str_hash = obj_reaData.hash_;	// 下载用的参数
	
	for( var i = 0; i < n_searchLen; i++ ) {	
		var obj_tempData = obj_searchData[i], 
			str_id =  obj_tempData.id;
		
		switch (str_who) {
			case 'operator': // 操作员查询
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
			case 'eventSearch': // 告警查询
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
	
	if ( str_who == 'singleMileage' || str_who == 'singleEvent' ) {
		var obj_tfoot = $('.j_'+ str_who +'Foot'),
			obj_theadTH = $('.j_' + str_who + 'TH'),	// 表头时间TH
			n_type = parseInt($('#'+ str_who +'Type').val()),
			obj_content = $('.j_' + str_who + 'Content'),	// 内容区域
			obj_month = $('#'+ str_who +'Month'),
			b_month = obj_month.is(':hidden'),
			str_alias = $('.j_currentCar').text().substr(2),	// 当前定位器名称
			obj_chart = {'name': str_alias, 'data': arr_graphic}, 
			str_tfoot = '<tr><td>总计：</td>',
			arr_categories = [],
			str_unit = '次',
			str_container = 'singleEventChart',
			str_th = '日期',
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
		
		if ( !b_month && n_dwRecordPageNum != obj_reaData.pagecnt-1 ) {	// 如果是月报 &查询的是第一页：显示foot						
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
			
			obj_content.css('height', '400px');
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
		obj_stTime = $('#'+str_inputStartTime), 
		obj_endTime = $('#'+str_inputEndTime);
	
	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联
		WdatePicker({el: str_inputStartTime, dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, maxDate: '#F{$dp.$D(\''+str_inputEndTime+'\')}', qsEnabled: false,
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
	}).val(str_nowDate+' 00:00:00');
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: str_inputEndTime, dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, minDate: '#F{$dp.$D(\''+str_inputStartTime+'\')}', qsEnabled: false, 
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
	}).val(str_nowDate+' '+dlf.fn_changeNumToDateString(n_currentDate, 'sfm'));
	
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
		n_month = obj_date.getMonth() + 1;		// 当前月份
	
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
				str_options += '<option value="'+ m +'">'+ m +'月</options>';
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