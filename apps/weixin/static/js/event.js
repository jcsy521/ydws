/*
* 告警查询功能 
*/
var n_showItemNums = 0,
	n_showItemMaxNums = 0;
	
$(function() {		
	$('#loadDatasTHeader').nextAll().remove();
	$('#loadEventDatas').hide();
	
	$('#eventSearch_btn').removeData('eventdata');
	
	// 查询数据
	$('#eventBtn_day').click(function(e) {
		fn_loadEventData('day');
	});
	$('#eventBtn_week').click(function(e) {
		fn_loadEventData('week');
	});
	
	
	// 加载数据
	$('#loadEventDatas').click(function(){
		var srollPos = $(window).scrollTop(), //滚动条距离顶部的高度
			windowHeight = $(window).height(), //窗口的高度
			dbHiht = $('body').height(); //整个页面文件的高度
		
		$('#loadEventDatas').html('加载中...');
		
		if((windowHeight + srollPos) >= (dbHiht) && n_showItemNums != n_showItemMaxNums){
			fn_addDataList();
			if ( n_showItemNums >= n_showItemMaxNums ) {
				$('#loadEventDatas').hide;
			} else {
				$('#loadEventDatas').show().html('加载更多');
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
	$('#loadEventDatas').hide();
	
	if ( str_timeType == 'day' ) {
		n_stTime = toEpochDate(str_today+' 00:00:00');
		n_endTime = n_nowTime;
	} else if ( str_timeType == 'week' ) {
		n_stTime = n_nowTime - 7*n_dayTimel;
		n_endTime = n_nowTime;
	}
	obj_eventData.start_time = parseInt(n_stTime);
	obj_eventData.end_time = parseInt(n_endTime);
	
	$.post_('/event', JSON.stringify(obj_eventData), function(data) {
		if ( data.status == 0 ) {
			$('#eventSearch_btn').data('eventdata', data.res);
			
			n_showItemMaxNums = data.res.length;
			
			fn_addDataList();
			
			if ( n_showItemMaxNums > 10 ) {
				$('#loadEventDatas').show().html('加载更多');
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
			var obj_tempData = arr_eventData[n_showItemNums];
			
			if ( obj_tempData ) {
				str_showHtml += '<tr>';
				str_showHtml += '<td>'+ fn_NumForRound(obj_tempData.speed, 1) +'</td>';
				str_showHtml += '<td>'+ fn_NumForRound(obj_tempData.clongitude/3600000, 3) +', '+ fn_NumForRound(obj_tempData.clatitude/3600000, 3) +'</td>';
				
				if (  obj_tempData.name == '' ) {
					str_showHtml += '<td></td>';
				} else {
					str_showHtml += '<td><a href="#" onclick=fn_eventNameDetail('+ n_showItemNums +')'+ fn_NumForRound(obj_tempData.name, 6) +'</a></td>';
				}
				str_showHtml += '</tr>';
			}
			n_showItemNums++; //计数器+1
		}
		$('#loadDatasTHeader').after(str_showHtml);
		$(window).scrollTop($(window).height()+100);
	}
	$('#loadEventDatas').hide();
}

// 显示地址详细信息
function fn_eventNameDetail(n_itemIndex) {
	var data = $('#eventSearch_btn').data('eventdata'),
		obj_itemData = data[n_showItemNums];
	
	if ( obj_itemData ) {
		alert(obj_itemData.name);
	}
	
}
