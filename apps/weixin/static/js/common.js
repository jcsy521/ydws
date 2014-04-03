/*
* 公共方法集合
*/

// 返回当天的日期的UTC表示:例如2010-11-05 只判断日期
function toTodayDate() { 
	var myDate = new Date();
	myDate.setTime(myDate.getTime()); //-24*60*60*1000);
	var year = myDate.getFullYear();
	var month = myDate.getMonth() + 1;
	var day = myDate.getDate();
	if (month < 10) {
		month = '0' + month;
	}
	if (month == 0) {
		month = 12;
	}
	if (day < 10) {
		day = '0' + day;
	}
	return year + '-' + month + '-' + day;
}

// 将UTC时间转为正常时区时间
function toHumanDate(myEpoch, flag) { 
	if ( !myEpoch ) {
		return '';
	}
	var myDate = new Date(Number(myEpoch)*1000);
	var year = myDate.getFullYear();
	var month = myDate.getMonth() + 1;
	var day = myDate.getDate();
	var hours = myDate.getHours();
	var min = myDate.getMinutes();
	var seconds = myDate.getSeconds();
	if (month < 10) {
		month = '0' + month;
	}
	if (month == 0) {
		month = 12;
	}
	if (day < 10) {
		day = '0' + day;
	}
	if (hours < 10) {
		hours = '0' + hours;
	}
	if (min < 10) {
		min = '0' + min;
	}
	if (seconds < 10) {
		seconds = '0' + seconds;
	}
	if ( flag == 'year' ) {
		return year;
	} else if ( flag == 'month' ) {
		return month;
	} else if ( flag == 'day' ) {
		return day;
	}else if (flag == 'no') {
		return year + '-' + month + '-' + day;//2010-09-10 z
	} else {
		return year + '-' + month + '-' + day + ' ' + hours + ':' + min + ':' + seconds;
	}
}

// 将正常时区时间转为UTC时间
function toEpochDate(dateString) { 
	var tmp = dateString;
	var tmpArr;
	if (tmp != null && tmp != '') {
		tmpArr = tmp.split(' ');
		var dateArr = tmpArr[0].split('-');
		var year = dateArr[0];
		var month = dateArr[1];
		var day = dateArr[2];
		var timeArr = tmpArr[1].split(':');
		var hour = timeArr[0];
		var min = timeArr[1];
		var seconds = timeArr[2];
		var myDate = new Date(year,month - 1,day,hour,min,seconds); // Your timezone!
		var myEpoch = myDate.getTime() / 1000;
		return myEpoch;
	}
}

/*
* 对给定的数值进行小数位截取
* n_num: 要操作的数字
* n_round: 小数后保留的位数
*/
function fn_NumForRound(n_num, n_round) {
	var n_roundNum = 1;
	
	if ( n_round != 0 ) {
		for ( var i = 1; i <= n_round; i++ ) {
			n_roundNum = n_roundNum * 10
		}
	}
	return Math.round(n_num * n_roundNum) / n_roundNum;
}

/**
* 根据相应的报警状态码显示相应的报警提示
*/
function fn_eventText (n_eventNum) {
	var str_text = '无法获取';
	
	switch (n_eventNum) {
		case 2:
			str_text = '电量';	// 告警
			break;
		case 3:
			str_text = '震动';
			break;
		case 4:
			str_text = '移动';
			break;
		case 5:
			str_text = 'SOS';
			break;
		case 6:
			str_text = '通讯异常';
			break;
		case 7:
			str_text = '进围栏';
			break;
		case 8:
			str_text = '出围栏';
			break;
		case 9:
			str_text = '断电';
			break;
		case 10:
			str_text = '停留';
			break;
	}
	return str_text;
}

// 添加遮罩层并显示消息
function fn_dialogMsg(str_msg, n_msgTime) {
	$('#ioverlay, #pageMsg').show();
	
	$('#pageMsg').html(str_msg);
	if ( n_msgTime ) {
		setTimeout(function() {
			fn_closeDialogMsg();
		}, n_msgTime);
	}
}

// 关闭遮罩层
function fn_closeDialogMsg() {
	$('#ioverlay, #pageMsg').hide();
}

/**
* jquery 异步请求架构
* url: ajax请求的url
* data: ajax请求参数
* callback: 回调函数
* errorCallback: 出现错误的回调函数
* method： ajax请求方式get or post
*/
function _ajax_request(url, data, callback, errorCallback, method) {
	return jQuery.ajax({
		type : method,
		url : url,
		data : data,
		success : callback,
        error : errorCallback, // 出现错误
		dataType : 'json',
		contentType : 'application/json; charset=utf-8',
        complete: function (XMLHttpRequest, textStatus) { 
           
        }
	});
}

/**
* 处理请求服务器错误
*/
function fn_serverError(XMLHttpRequest, str_actionType) {
	var str_errorType = XMLHttpRequest.statusText;
	
	if ( str_errorType == 'timeout' ) {
		alert('网络繁忙，请稍后重试。');
		return;
	}
}

/**
* 继承并重写jquery的异步方法
*/
jQuery.extend({
    put_: function(url, data, callback, errorCallback) {
        return _ajax_request(url, data, callback, errorCallback, 'PUT');
    },
    delete_: function(url, data, callback, errorCallback) {
        return _ajax_request(url, data, callback, errorCallback, 'DELETE');
    },
    post_: function(url, data, callback, errorCallback) {
        return _ajax_request(url, data, callback, errorCallback, 'POST');
    },
	get_: function(url, data, callback, errorCallback) {
        return _ajax_request(url, data, callback, errorCallback, 'GET');
    }
});