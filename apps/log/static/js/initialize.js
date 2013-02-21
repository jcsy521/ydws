var n_pageNum = 0, n_pageCnt = -1; // 页面初始查询 
$(function () {
	// 设置标题头样式
	$('#loghistory th').addClass('ui-state-default');
	
	// 用户名及退出的显示位置
	$('.right_title').css('left', (document.body.clientWidth - 230)+ 'px');
	
	// 设置默认时间
 	$("#beginDate").val(fn_fomratDate());
 	$("#endDate").val(fn_fomratDate('today'));
	
	// 页面点数元素的对象
	$logPageNum = $('#loghistory_pagenum'), $logPageCnt = $('#loghistory_next');
	// 上一页
	$('#loghistory_previous').click(function () {
		if (n_pageNum <= 0) {
			return;
		}
		$logPageNum.text(--n_pageNum+1);
		fn_getLogData();
	});
	// 下一页
	$('#loghistory_next').click(function () {
		if (n_pageNum >= n_pageCnt-1) {
			return;
		}
		$logPageNum.text(++n_pageNum+1);
		fn_getLogData();								  
	});
	//查询
	$('#logSearch').click(function () {
		n_pageNum = 0;
		n_pageCnt = -1;						  
		fn_getLogData();
	});
	// 退出询问
	$('#logout').click(function () {
		if (confirm('您确定退出本系统吗？')) {
			window.location.href = '/logout'; 
		}
	});
});
// 当用户窗口改变时,地图做相应调整
window.onresize = function () {
    setTimeout (function () {
		// 用户名及退出的显示位置
		$('.right_title').css('left', (document.body.clientWidth - 230)+ 'px');
	}, 1);
}
// 日期计算
function fn_fomratDate(str_flag) {
	var d_date = null;
	if (str_flag == 'today') {
		d_date = new Date();
	} else {
		d_date = new Date(new Date().getTime() - 24*60*60*1000);
	}
	var year = d_date.getFullYear(); // 注意
 	var month = d_date.getMonth()+1;
 	var day = d_date.getDate();
 	var hour = d_date.getHours();
 	var minute = d_date.getMinutes();
 	var second = d_date.getSeconds();
	minute = minute < 10 ? '0'+ minute : minute;
	second = second < 10 ? '0'+ second : second;
	return year+"-"+month+"-"+day+" "+hour+":"+minute+":"+second;
}
// 向后台要数据方法
function fn_getLogData() {
	if (fn_validCookie()) {
		return;
	};
	var obj_pd = null, str_stTime = $('#beginDate').val(), str_entTime = $('#endDate').val(), 
		str_planId = $('#plan_id').val(), str_levelId = $('#level_id').val();
	obj_pd = {
		'beginDate': str_stTime,
		'endDate': str_entTime,
		'plan_id': str_planId,
		'pagenum': n_pageNum,
		'pagecnt': n_pageCnt,
		'level': str_levelId
	}
	$.post('/systemlog',  JSON.stringify(obj_pd), function (data) {
		if (data.status == 0) {
			var obj_data = data.loglist, n_len = obj_data.length, html = '', $tBody = $('#loghistory_tbody'), 
				$pageNum = $('#loghistory_pagenum'), $pageCnt = $('#loghistory_pagecnt');
			if (n_len > 0) {
				n_pageCnt = data.pagecnt;
				$tBody.nextAll().remove(); // 移除页面数据
				if (n_pageNum == 0) {
					$pageNum.html('1');
					$pageCnt.html(n_pageCnt);
				}
				for (var i = 0; i < n_len; i++) {
					var obj_tempData = obj_data[i];
					if (i % 2 != 0) {
						html += '<tr class="odd">';
					} else {
						html += '<tr class="even">';
					}
					html += '<td class=" sorting_1">'+obj_tempData.time+'</td>';
					html += '<td>'+obj_tempData.servername+'</td>';
					html += '<td>'+obj_tempData.level+'</td>';
					html += '<td class="logContent">'+obj_tempData.details+'</td>';
					html += '<td><a href="/detail?id='+obj_tempData.id+'" target="_blank" >查看详细</a></td></tr>';
				}
			} else {
				html += '<tr class="odd" style="text-align: center;"><td colspan="5">无记录</td></tr>';
			}
			$tBody.html(html);
		} else { // 连接服务器错误
			alert(data.message);
		}
		
	});
}
function fn_validCookie() {
	// 验证cookie是否超时
	if(!$.cookie('ACBLOGSYSTEM')) {
		window.location.replace('/'); // redirect to the index.
		return true;
	}
	return false;
}