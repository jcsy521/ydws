/**
*告警相关操作方法
*/
var arr_eventData = [],	// 后台查询到的报警记录数据
	pagecnt = -1,	// 查询到数据的总页数,默认-1
	n_pageNum = 0;	// 当前所在页数
	
/**
* 初始化告警查询
* n_num: 本次要查第几页的数据
*/
function fn_initEventSearch(n_num) {
	var n_startTime = $('#eventStartTime').val(), // 用户选择时间
		n_endTime = $('#eventEndTime').val(), // 用户选择时间
		n_bgTime = dlf.fn_changeDateStringToNum(n_startTime), // 开始时间
		n_finishTime = dlf.fn_changeDateStringToNum(n_endTime), //结束时间
		n_category = $('#category').val(), 
		obj_eventParam = {'start_time': n_bgTime, 'end_time': n_finishTime, 
				'pagenum': n_pageNum, 'pagecnt': pagecnt, 'category': n_category};
	
	dlf.fn_closeDialog(); // 小地图提示窗口关闭
	dlf.fn_jNotifyMessage('告警记录查询中' + WAITIMG, 'message', true);	
	dlf.fn_lockScreen('eventbody'); // 添加页面遮罩
	$('.eventbody').data('layer', true);	// 查询中时如果窗口改变大小，遮罩层也做相应修改
	
	$.post_(EVENT_URL, JSON.stringify(obj_eventParam), function(data) {	// 获取告警记录信息
		if ( data.status == 0 ) {  // success
			var obj_prevPage = $('#prevPage'), 
				obj_nextPage = $('#nextPage'),
				n_eventDataLen = 0,
				str_tbodyText = '';
				
			$('#eventTableHeader').nextAll().remove();	//清除页面数据
			pagecnt = data.pagecnt;
			arr_eventData = data.events;
			n_eventDataLen = arr_eventData.length; 	//记录数
			
			if ( n_eventDataLen > 0 ) {	// 如果查询到数据
				$('#pagerContainer').show(); //显示分页
				if ( pagecnt > 1 ) {	// 总页数大于1 
					if ( n_num > 0 && n_num < pagecnt-1 ) {  //上下页都可用 
						dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage0', 'prevPage1'));
						dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage0', 'nextPage1'));
					} else if ( n_num >= pagecnt-1 ) {	//下一页不可用						
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
				
				if ( n_num == 0 ) {	// 只有在点击查询按钮时才重新显示总页数
					$('#pageCount').text(data.pagecnt); //总页数
					$('#currentPage').html('1');	//当前页数
				}
				for(var i = 0; i < n_eventDataLen; i++) {
					var obj_location = arr_eventData[i], 
						str_type = obj_location.category,	//类型
						n_lng = obj_location.clongitude,
						n_lat = obj_location.clatitude,
						str_location = obj_location.name, 
						str_text = '';	//地址
					
					/**
					* 拼接table
					*/
					str_tbodyText+= '<tr>';
					str_tbodyText+= '<td>'+dlf.fn_changeNumToDateString(obj_location.timestamp)+'</td>';	// 告警时间
					str_tbodyText+= '<td>'+dlf.fn_eventText(str_type)+'</td>';	// 告警类型
					if ( n_lng == 0 || n_lat == 0 ) {	//无地址
						str_tbodyText+= '<td>无</td>';	
					} else {
						if ( str_location == '' || str_location == null ) {
							str_tbodyText+= '<td><a href="#"   onclick="dlf.fn_getAddressByLngLat('+n_lng+', '+n_lat+',this);">获取位置</a></td>';
						} else {
							str_tbodyText+= '<td><a href="#" c_lon="'+n_lng+'" c_lat="'+n_lat+'" class="j_eventItem">'+str_location+'</a></td>';	//详细地址
						}
					}
					str_tbodyText+= '</tr>';
				}
				$('#eventTableHeader').after(str_tbodyText);
				
				/** 
				* 初始化奇偶行
				*/
				$('.dataTable tr').mouseover(function() {
					$(this).css('background-color', '#FFFACD');
				}).mouseout(function() {
					$(this).css('background-color', '');
				});
				
				/**
				* 用户点击位置进行地图显示
				*/
				$('.j_eventItem').click(function(event) {
					dlf.fn_clearMapComponent();
					$('.eventMapContent').css({	// 小地图显示位置
						'left': event.clientX+20, 
						'top': event.clientY		
					}).show();
					/**
					* 根据行编号拿到数据，在地图上做标记显示
					*/
					var n_tempIndex = $(this).parent().parent().index()-1,
						obj_tempData = arr_eventData[n_tempIndex];
					
						obj_tempData.alias = $('.eventbody').attr('alias');
						dlf.fn_addMarker(obj_tempData, 'eventSurround', 0, true); // 添加标记
						setTimeout (function () {
							var obj_centerPointer = new BMap.Point(obj_tempData.clongitude/NUMLNGLAT, obj_tempData.clatitude/NUMLNGLAT);
							mapObj.centerAndZoom(obj_centerPointer, 17);
						}, 100);
				});
				dlf.fn_closeJNotifyMsg('#jNotifyMessage');
			} else {
				$('#pagerContainer').hide(); //显示分页
				dlf.fn_jNotifyMessage('该时间范围内没有告警记录', 'message', false, 6000);
			}
			dlf.fn_unLockScreen(); // 去除页面遮罩
			$('.eventbody').removeData('layer');
		} else if ( data.status == 201 ) {	// 业务变更
			dlf.fn_showBusinessTip('event');
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);	
		}
	},
	function(XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

/**
* 当用户窗口改变时,地图做相应调整
*/
window.onresize = function () {
    setTimeout (function () {
		$('.eventbody').css({	// 调整BODY高度
			'height': $(window).height() - 10,
			'width': $(window).width()
		});
		var f_layer = $('.eventbody').data('layer');
		if ( f_layer ) {	// 是否对遮罩做修改
			dlf.fn_lockScreen('eventbody');
		}
	}, 25);
}

/**
* event页面加载完成后进行加载地图
*/
$(function () {
	dlf.fn_loadMap();	// 加载MAP
	mapObj.removeControl(viewControl);  //隐藏鹰眼
	
	$('.eventbody').css({	// 调整BODY高度
		'height': $(window).height() - 10,
		'width': $(window).width()
	});	
	
	/**
	* 初始化报警查询选择时间
	*/
	var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime(), 'ymd'), 
		obj_stTime = $('#eventStartTime'), 
		obj_endTime = $('#eventEndTime');
		
	obj_stTime.click(function() {	// 初始化起始时间，并做事件关联
		WdatePicker({el: 'eventStartTime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, maxDate: '#F{$dp.$D(\'eventEndTime\')}', qsEnabled: false, 
			onpicked: function() {
				var obj_endDate = $dp.$D('eventEndTime'), 
					str_endString = obj_endDate.y+'-'+obj_endDate.M+'-'+obj_endDate.d+' '+obj_endDate.H+':'+obj_endDate.m+':'+obj_endDate.s,
					str_endTime = dlf.fn_changeDateStringToNum(str_endString), 
					str_beginTime = dlf.fn_changeDateStringToNum($dp.cal.getDateStr());
				if ( str_endTime - str_beginTime > WEEKMILISECONDS) {
					obj_endTime.val(dlf.fn_changeNumToDateString(str_beginTime + WEEKMILISECONDS));
				}
			}
		});
	}).val(str_nowDate+' 00:00:00');
	
	obj_endTime.click(function() {	// 初始化结束时间，并做事件关联
		WdatePicker({el: 'eventEndTime', dateFmt: 'yyyy-MM-dd HH:mm:ss', readOnly: true, isShowClear: false, minDate:'#F{$dp.$D(\'eventStartTime\')}', qsEnabled: false, 
			onpicked: function() {
				var obj_beginDate = $dp.$D('eventStartTime'), 
					str_beginString = obj_beginDate.y+'-'+obj_beginDate.M+'-'+obj_beginDate.d+' '+obj_beginDate.H+':'+obj_beginDate.m+':'+obj_beginDate.s,
					str_beginTime = dlf.fn_changeDateStringToNum(str_beginString), 
					str_endTime = dlf.fn_changeDateStringToNum($dp.cal.getDateStr());
				if ( str_endTime - str_beginTime > WEEKMILISECONDS) {
					obj_stTime.val(dlf.fn_changeNumToDateString(str_endTime - WEEKMILISECONDS));
				}
			}
		});
	}).val(str_nowDate+' '+dlf.fn_changeNumToDateString(new Date(), 'sfm'));

	dlf.fn_closeWrapper(); //关闭地图位置显示框事件
	
	$('.eventMapContent').draggable({cursor:'move', containment: 'body', stop: function(event, ui) {	// 弹出的地图可以拖动
		if ( ui.position.top < 0 ) {
			$(this).css('top', 0);
		}
	}});
	$('#eventType option[value=-1]').attr('selected', true);	// 告警类型选项初始化
	
	/** 
	* 上一页按钮 下一页按钮
	*/
	var obj_prevPage = $('#prevPage'), 
		obj_nextPage = $('#nextPage'), 
		obj_currentPage = $('#currentPage'),
		obj_search = $('#eventSearch');
	
	/** 
	* 绑定按钮事件
	*/
	dlf.fn_setItemMouseStatus(obj_search, 'pointer', new Array('cx', 'cx2'));
	dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage2', 'prevPage1'));
	dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage2', 'nextPage1'));
	/**
	* 上下页事件绑定
	*/
	obj_prevPage.click(function() {
		if ( n_pageNum <= 0) {
			return;
		}
		obj_currentPage.text(--n_pageNum+1);
		fn_initEventSearch(n_pageNum);
	});
	obj_nextPage.click(function() {
		if ( n_pageNum >= pagecnt-1 ) {
			return;
		}
		obj_currentPage.text(++n_pageNum+1);
		fn_initEventSearch(n_pageNum);
	});
	
	obj_search.click(function() {	// 告警记录查询事件
		pagecnt = -1;
		n_pageNum = 0;
		fn_initEventSearch(n_pageNum);
	});
})