/*
*报警相关操作方法
*/
var pagecnt = -1,
	n_pageNum = 0;
//初始化轨迹查询
function fn_initEventSearch(n_num, n_et) {
	dlf.fn_closeDialog(); // 小地图提示窗口关闭
	dlf.fn_jNotifyMessage('报警记录查询中...<img src="/static/images/blue-wait.gif" />', 'message', true);	
	dlf.fn_lockScreen('eventbody'); // 添加页面遮罩
	$('.eventbody').data('layer', true);
	
	var n_time = $('#eventTime').val(), // 用户选择时间
		n_bgTime = dlf.fn_changeDateStringToNum(n_time+' 00:00:00'), // 开始时间
		n_endTime = dlf.fn_changeDateStringToNum(n_time+' 23:59:59'), //结束时间
		n_carId = $('#eventResult').attr('tid'),	//car_id
		n_eventType = $('#eventType').val(), 
		param = {'start_time': n_bgTime, 'end_time': n_endTime, 'tid' : n_carId, 
				'pagenum': n_pageNum, 'pagecnt': pagecnt, 'event_type': n_eventType}; //  id

	//获取报警记录信息
	$.post_(EVENT_URL, JSON.stringify(param), function(data) {
		$('#eventTableHeader').nextAll().remove();	//清除页面数据
		pagecnt = data.pagecnt;
		var obj_prevPage = $('#prevPage'), 
			obj_nextPage = $('#nextPage');
			
		if ( data.status == 0 ) {  // success
			var n_len = data.events.length; 	//记录数
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
					var obj_location = data.events[i], 
						str_type = obj_location.category,	//类型
						str_location = obj_location.name, 
						str_text = '';	//地址
					
					// 拼接table
					html+= '<tr>';
					html+= '<td>'+dlf.fn_changeNumToDateString(obj_location.timestamp)+'</td>';	// 报警时间
					html+= '<td>'+dlf.fn_eventText(str_type)+'</td>';	//类型 // todo 
					if ( obj_location.clongitude == 0 || obj_location.clatitude == 0 ) {
						html+= '<td>无</td>';	//无地址
					} else {
					html+= '<td><a href="#" c_lon="'+obj_location.clongitude+'" c_lat="'+obj_location.clatitude+'" class="j_eventItem">'+str_location+'</a></td>';	//详细地址
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
					
					var str_imgUrl = '/static/images/default-marker.png', 
						myIcon = new BMap.Icon(str_imgUrl, new BMap.Size(20, 32)), 
						mPoint = new BMap.Point($(this).attr('c_lon')/NUMLNGLAT, $(this).attr('c_lat')/NUMLNGLAT), 
						marker= new BMap.Marker(mPoint, {icon: myIcon});
					
					mapObj.addOverlay(marker);//向地图添加覆盖物
					setTimeout (function () {
						mapObj.centerAndZoom(mPoint, 17);
					}, 100);
				});
				dlf.fn_closeJNotifyMsg('#jNotifyMessage');
			} else {
				$('#pagerContainer').hide(); //显示分页
				dlf.fn_jNotifyMessage('该时间范围内没有报警记录', 'message', false, 6000);
			}
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
	var str_nowDate = dlf.fn_changeNumToDateString(new Date().getTime()/1000, 'ymd');
	$('#eventTime').click(function() {
		WdatePicker({dateFmt: 'yyyy-MM-dd', readOnly: true, isShowClear: false, maxDate: '%y-%M-%d'});
	}).val(str_nowDate);
	
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