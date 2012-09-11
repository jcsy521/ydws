/*
*报警相关操作方法
*/
var arr_eventData = [],
	pagecnt = -1,
	n_pageNum = 0;
//初始化轨迹查询
function fn_initEventSearch(n_num, n_et) {
	dlf.fn_closeDialog(); // 小地图提示窗口关闭
	dlf.fn_jNotifyMessage('报警记录查询中...<img src="/static/images/blue-wait.gif" />', 'message', true);	
	dlf.fn_lockScreen('eventbody'); // 添加页面遮罩
	$('.eventbody').data('layer', true);
	
	var n_startTime = $('#eventStartTime').val(), // 用户选择时间
		n_endTime = $('#eventEndTime').val(), // 用户选择时间
		n_bgTime = dlf.fn_changeDateStringToNum(n_startTime), // 开始时间
		n_finishTime = dlf.fn_changeDateStringToNum(n_endTime), //结束时间
		n_category = $('#category').val(), 
		param = {'start_time': n_bgTime, 'end_time': n_finishTime, 
				'pagenum': n_pageNum, 'pagecnt': pagecnt, 'category': n_category};
	//获取报警记录信息
	$.post_(EVENT_URL, JSON.stringify(param), function(data) {
		$('#eventTableHeader').nextAll().remove();	//清除页面数据
		pagecnt = data.pagecnt;
		var obj_prevPage = $('#prevPage'), 
			obj_nextPage = $('#nextPage');
		if ( data.status == 0 ) {  // success
			arr_eventData = data.events;
			var n_len = arr_eventData.length; 	//记录数
			if ( n_len > 0 ) {
				$('#pagerContainer').show(); //显示分页
				// 总页数>1 
				if ( pagecnt > 1 ) {
					if ( n_num > 0 && n_num < pagecnt-1 ) {  
						//上下页都可用
						dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage0', 'prevPage1', 'prevPage0'));
						dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage0', 'nextPage1', 'nextPage0'));
					} else if ( n_num >= pagecnt-1 ) {
						//下一页不可用
						dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage0', 'prevPage1', 'prevPage0'));
						dlf.fn_setItemMouseStatus(obj_nextPage, 'default', 'nextPage2');
					} else {
						//上一页不可用
						dlf.fn_setItemMouseStatus(obj_prevPage, 'default', 'prevPage2');
						dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage0', 'nextPage1', 'nextPage0'));
					}				
				} else {
					//上下页都不可用
					dlf.fn_setItemMouseStatus(obj_prevPage, 'default', 'prevPage2');
					dlf.fn_setItemMouseStatus(obj_nextPage, 'default', 'nextPage2');
				}
				
				var html = '';
				// 只有在点击查询按钮时才重新显示总页数
				if ( n_num == 0 ) {
					$('#pageCount').text(data.pagecnt); //总页数
					$('#currentPage').html('1');	//当前页数
				}
				for(var i = 0; i < n_len; i++) {
					var obj_location = arr_eventData[i], 
						str_type = obj_location.category,	//类型
						n_lng = obj_location.clongitude,
						n_lat = obj_location.clatitude,
						str_location = obj_location.name, 
						str_text = '';	//地址
					
					// 拼接table
					html+= '<tr>';
					html+= '<td>'+dlf.fn_changeNumToDateString(obj_location.timestamp)+'</td>';	// 报警时间
					html+= '<td>'+dlf.fn_eventText(str_type)+'</td>';	//类型 // todo 
					if ( n_lng == 0 || n_lat == 0 ) {
						html+= '<td>无</td>';	//无地址
					} else {
						if ( str_location == '' || str_location == null ) {
							html+= '<td><a href="#"   onclick="dlf.fn_getAddressByLngLat('+n_lng+', '+n_lat+',this);">获取位置</a></td>';
						} else {
							html+= '<td><a href="#" c_lon="'+n_lng+'" c_lat="'+n_lat+'" class="j_eventItem">'+str_location+'</a></td>';	//详细地址
						}
					}
					html+= '</tr>';
				}
				$('#eventTableHeader').after(html);
				
				//初始化奇偶行
				$('.dataTable tr').mouseover(function() {
					$(this).css('background-color', '#FFFACD');
				}).mouseout(function() {
					$(this).css('background-color', '');
				});
				
				// 用户点击位置进行地图显示
				$('.j_eventItem').click(function(event) {
					dlf.fn_clearMapComponent();
					$('.eventMapContent').css({
						'left': event.clientX+20, 
						'top': event.clientY		
					}).show();
					
					var n_tempIndex = $(this).parent().parent().index()-1,
						obj_tempData = arr_eventData[n_tempIndex];
					
						//obj_tempData.tid = n_carId;
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
				dlf.fn_jNotifyMessage('该时间范围内没有报警记录', 'message', false, 6000);
			}
		} else if ( data.status == 201 ) {
			dlf.fn_showBusinessTip();
		} else {
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);	
		}
		dlf.fn_unLockScreen(); // 去除页面遮罩
		$('.eventbody').removeData('layer');
	},
	function(XMLHttpRequest, textStatus, errorThrown) {
		dlf.fn_serverError(XMLHttpRequest);
	});
}

// 当用户窗口改变时,地图做相应调整
window.onresize = function () {
    setTimeout (function () {
		// 调整BODY高度
		$('.eventbody').css({
			'height': $(window).height() - 10,
			'width': $(window).width()
		});
		var f_layer = $('.eventbody').data('layer');
		if ( f_layer ) {
			dlf.fn_lockScreen('eventbody');
		}
	}, 25);
}

// 页面加载完成后进行加载地图
$(function () {
	// 加载MAP
	dlf.fn_loadMap();
	mapObj.removeControl(viewControl); //隐藏鹰眼
	
	// 调整BODY高度
	$('.eventbody').css({
		'height': $(window).height() - 10,
		'width': $(window).width()
	});	
	// 初始化时间
	var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime(), 'ymd'), 
		obj_stTime = $('#eventStartTime'), 
		obj_endTime = $('#eventEndTime');
		
	obj_stTime.click(function() {
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
	obj_endTime.click(function() {
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
	// 弹出的地图可以拖动
	$('.eventMapContent').draggable({cursor:'move', handle: 'h2', containment: 'body', stop: function(event, ui) {
		if ( ui.position.top < 0 ) {
			$(this).css('top', 0);
		}
	}});
	// 报警类型选项初始化
	$('#eventType option[value=-1]').attr('selected', true);
	
	//上一页按钮 下一页按钮
	var obj_prevPage = $('#prevPage'), 
		obj_nextPage = $('#nextPage'), 
		obj_currentPage = $('#currentPage'),
		obj_search = $('#eventSearch');
	
	// 按钮变色
	dlf.fn_setItemMouseStatus(obj_search, 'pointer', new Array('cx', 'cx2', 'cx'));
	dlf.fn_setItemMouseStatus(obj_prevPage, 'pointer', new Array('prevPage2', 'prevPage1', 'prevPage0'));
	dlf.fn_setItemMouseStatus(obj_nextPage, 'pointer', new Array('nextPage2', 'nextPage1', 'nextPage0'));
	//上一页分页		
	obj_prevPage.click(function() {
		if ( n_pageNum <= 0) {
			return;
		}
		obj_currentPage.text(--n_pageNum+1);
		fn_initEventSearch(n_pageNum, pagecnt);
	});
	//下一页分页
	obj_nextPage.click(function() {
		if ( n_pageNum >= pagecnt-1 ) {
			return;
		}
		obj_currentPage.text(++n_pageNum+1);
		fn_initEventSearch(n_pageNum, pagecnt);
	} );
	
	// 报警记录查询事件
	obj_search.click(function() {
		pagecnt = -1;
		n_pageNum = 0;
		fn_initEventSearch(n_pageNum, pagecnt);
	});
})