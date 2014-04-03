/*
* 告警查询功能 
*/
var n_showItemNums = 0,
	n_showItemMaxNums = 0;
	
$(function() {	
	$('#loadDatasTHeader').nextAll().remove();
	$('#loadEventDatas, #loadEventNoDatas').hide();
	
	$('#eventSearch_btn').removeData('eventdata');
	
	$('#eventBtn_week, #eventBtn_day').removeClass('currentEventBtn');
	
	// 查询数据
	$('#eventBtn_day').click(function(e) {
		fn_loadEventData('day');
		$('#eventBtn_week').removeClass('currentEventBtn');
		$(this).addClass('currentEventBtn');
	});
	$('#eventBtn_week').click(function(e) {
		fn_loadEventData('week');
		$('#eventBtn_day').removeClass('currentEventBtn');
		$(this).addClass('currentEventBtn');
	});
	
	//切换查询的终端 ,清除数据
	$('#terminalList').change(function(e) {
		$('#loadDatasTHeader').nextAll().remove();
		$('#loadEventDatas, #loadEventNoDatas, #loadDatas').hide();
		$('#eventSearch_btn').removeData('eventdata');
	});
	
	// 加载数据
	$('#loadEventDatas').click(function(){
		var srollPos = $(window).scrollTop(), //滚动条距离顶部的高度
			windowHeight = $(window).height(), //窗口的高度
			dbHiht = $('body').height(); //整个页面文件的高度
		
		$('#loadEventDatas').val('数据加载中');
		
		if((windowHeight + srollPos) >= (dbHiht) && n_showItemNums != n_showItemMaxNums){
			fn_addDataList();
			if ( n_showItemNums >= n_showItemMaxNums ) {
				$('#loadEventDatas').hide;
			} else {
				$('#loadEventDatas').show().val('加载更多');
			}
			
		}
	});
});

// 加载数据
function fn_loadEventData(str_timeType) {
	var str_tid = $('#terminalList').val(),
		str_openid = $('#openid').val(),
		n_stTime = 0,
		n_endTime = 0,
		obj_eventData = {'tid': str_tid, 'openid': str_openid, 'start_time': 0, 'end_time': 0},
		str_today = toTodayDate(),
		n_nowTime = new Date().getTime()/1000,
		n_dayTimel = 60*60*24;
	
	$('#loadDatasTHeader').nextAll().remove();
	$('#loadEventDatas, #loadEventNoDatas, #loadDatas').hide();
	
	if ( str_timeType == 'day' ) {
		n_stTime = toEpochDate(str_today+' 00:00:00');
		n_endTime = n_nowTime;
	} else if ( str_timeType == 'week' ) {
		n_stTime = n_nowTime - 7*n_dayTimel;
		n_endTime = n_nowTime;
	}
	obj_eventData.start_time = parseInt(n_stTime);
	obj_eventData.end_time = parseInt(n_endTime);
	
	$('#loadEventNoDatas').hide();
	
	fn_dialogMsg('数据加载中<img src="/static/images/blue-wait.gif" />');
	$.post_('/event', JSON.stringify(obj_eventData), function(data) {
		fn_closeDialogMsg();
		if ( data.status == 0 ) {
			n_showItemNums = 0,
			n_showItemMaxNums = 0;
			$('#eventSearch_btn').data('eventdata', data.res);
			
			n_showItemMaxNums = data.res.length;
			
			if ( n_showItemMaxNums > 0 ) {
				$('#loadDatas').show();
				fn_addDataList();
			} else {				
				$('#loadEventNoDatas').show();
			}
		} else {
			alert(data.message);
		}
	});
}

// 加载更多数据
function fn_addDataList() {
	var str_showHtml = '',
		arr_eventData = $('#eventSearch_btn').data('eventdata');
	
	if ( arr_eventData ) {
		for ( var i = 0; i < 10; i++) {
			var obj_tempData = arr_eventData[n_showItemNums],
				str_tdCls = '#eaebff';
			
			if ( obj_tempData ) {
				str_showHtml += '<tr class="'+ str_tdCls +'">';
				str_showHtml += '<td>'+ toHumanDate(obj_tempData.timestamp, 'yes') +'</td>';
				str_showHtml += '<td>'+ fn_eventText(obj_tempData.category, 1) +'</td>';
				str_showHtml += '</tr>';
			}
			n_showItemNums++; //计数器+1
		}
		$('#loadDatasTHeader').after(str_showHtml);
		$(window).scrollTop($(window).height()*parseInt(n_showItemNums/10)+200);
	}
	
	if ( n_showItemMaxNums > n_showItemNums ) {
		$('#loadEventDatas').show().val('加载更多');
	} else {
		$('#loadEventDatas').hide();
	}
}

