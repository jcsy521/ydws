$(function () {
	// 设置标题头样式
	$('#search_table th').addClass('ui-state-default');
	
	// 用户名及退出的显示位置
	$('.right_title').css('left', (document.body.clientWidth - 230)+ 'px');
	
	// 初始化时间插件及表格
	var str_who = $('#search_table').attr('whois');
	
	if ( str_who == 'log' || str_who == 'packet' || str_who == 'battery' || str_who == 'feedback' ) {
		// 设置默认时间
		fn_initTimeControl(str_who);
		fn_initRecordSearch(str_who);
	}
	
	// 退出询问
	$('#logout').click(function () {
		if (confirm('您确定退出本系统吗？')) {
			window.location.href = '/logout'; 
		}
	});
	
	// 窗口关闭，清除cookie
	window.close(function() {
		$.cookie('ACBLOGSYSTEM', null);
	});
});

/**
* 转化日期字符串为整数
* dateString格式有两种2011-11-11 20:20:20, 20:20
* 如果直传第二中小时和分钟，则在使用今天日期构造数据
* 返回秒
*/
function fn_changeDateStringToNum(dateString) {
    var year = '',
        month = '', 
        day = '', 
        hour = '', 
        min = '', 
        seconds = '00', 
        timeArr = '';

	if ( dateString.search('-') != -1 ) {
		var tmpArr = dateString.split(' '), 
            dateArr = tmpArr[0].split('-');

		year = dateArr[0], 
        month = dateArr[1]-1, 
        day = dateArr[2],
		timeArr = tmpArr[1].split(':'), 
        hour = timeArr[0], 
        min = timeArr[1], 
        seconds = timeArr[2];
	} else {
        var date = new Date();
			year = date.getFullYear(),
			month = date.getMonth(),
			day = date.getDate();
        
        month = month < 10 ? '0'+month : month;
        day = day < 10 ? '0'+day : day;
        
        timeArr = dateString.split(':'),
        hour = timeArr[0], 
        min = timeArr[1];
    }
	return new Date(year,month,day,hour,min,seconds).getTime()/1000; // Your timezone!
}

// 日期计算
function fn_changeNumToDateString(myEpoch) {
	var myEpoch = new Date(myEpoch*1000),
		year = myEpoch.getFullYear(); // 注意
 	var month = myEpoch.getMonth()+1;
 	var day = myEpoch.getDate();
 	var hour = myEpoch.getHours();
 	var minute = myEpoch.getMinutes();
 	var second = myEpoch.getSeconds();
	
	month = month < 10 ? '0'+month : month;
    day = day < 10 ? '0'+day : day;
	minute = minute < 10 ? '0'+ minute : minute;
	second = second < 10 ? '0'+ second : second;
	
	return year+"-"+month+"-"+day+" "+hour+":"+minute+":"+second;
}

/**
* 日期格式化
* 
*/
function fn_changeDateStringToFormat(dateString) {
	var tmpArr = dateString.split(' '),
		dateArr = tmpArr[0].split('-'),
		year = dateArr[0], 
		month = dateArr[1], 
		day = dateArr[2];
	
	return year+month+day+' '+tmpArr[1];
}
/**
*  时间控件初始化
*/
function fn_initTimeControl(str_who) {
	// 设置默认时间
	var obj_stTime = $('#beginDate'), 
		obj_endTime = $('#endDate'),
		obj_date = new Date(),
		n_year = obj_date.getFullYear(),
		n_month = obj_date.getMonth()+1,
		n_day = obj_date.getDate(),
		str_today = n_year + '-' + n_month + '-' + n_day + ' 00:00:00',
		MILISECONDS = 24*60*60*10*1000; // 10天的毫秒数;
		
	obj_stTime.datetimepicker({
		dateFormat: 'yy-mm-dd',
		timeFormat: 'HH:mm:ss',
		controlType: 'select',
		showSecond: true,
		onSelect: function (selectedDateTime){ 
			var n_startTime = obj_stTime.datetimepicker('getDate').getTime(),
				n_endTime = obj_endTime.datetimepicker('getDate').getTime(),
				n_timesDiff = n_endTime - n_startTime;
			
			if ( str_who != 'feedback' ) { 
				if ( Math.abs(n_timesDiff) > MILISECONDS ) {
					obj_endTime.datetimepicker('setDate', new Date(n_startTime + MILISECONDS));
				}
			}
		}
	});
	obj_endTime.datetimepicker({
		dateFormat: 'yy-mm-dd',
		timeFormat: 'HH:mm:ss',
		controlType: 'select',
		showSecond: true,
		onSelect: function (selectedDateTime){
			var n_startTime = obj_stTime.datetimepicker('getDate').getTime(),
				n_endTime = obj_endTime.datetimepicker('getDate').getTime(), 
				n_timesDiff = n_endTime - n_startTime;
				
			if ( str_who != 'feedback' ) { 
				if ( Math.abs(n_timesDiff) > MILISECONDS ) {
					obj_stTime.datetimepicker('setDate', new Date(n_endTime-MILISECONDS));
				}
			}
		}
	}); 
	if ( str_who == 'feedback' ) {
		obj_stTime.datetimepicker('setDate', str_today);
	} else {
		obj_stTime.datetimepicker('setDate', new Date( obj_date - 24*60*60*1000));
	}
	obj_endTime.datetimepicker('setDate', obj_date);
	
}

// 验证cookie是否超时
function fn_validCookie() {
	if(!$.cookie('ACBLOGSYSTEM')) {
		window.location.replace('/'); // redirect to the index.
		return true;
	}
	return false;
}

/*
* 调整标题用户名位置
*/
function fn_setTitleName() {
		var n_headWidth = $('.logHeader').width();
		
		$('.right_title').css('left', n_headWidth - 190);
}


/*
* 验证时间是否可以查询
*/
function fn_validSearchDate() {
	var str_beginTime = fn_changeDateStringToNum($('#beginDate').val()), 
		str_endTime = fn_changeDateStringToNum($('#endDate').val()),
		MILISECONDS = 24*60*60*10; // 10天的毫秒数;
	
	if ( str_beginTime >= str_endTime ) {
		alert('开始时间不能大于结束时间，请重新选择时间段。');
		return false;
	} else if ( str_endTime - str_beginTime > MILISECONDS ) {
		alert('最多只能查询10内天数据，请重新选择时间段。');
		return false;
	}
	return true;
}

/*
* 验证手机号是否合法
*/
function fn_validMobile(str_mobile, str_msgTitle) {
	var MOBILEREG = /^(\+86){0,1}1(3[0-9]|5[012356789]|8[023456789]|47)\d{8}$/,
		str_alertMsg = '终端';
	
	if ( str_msgTitle ) {
		str_alertMsg = str_msgTitle;
	}
	if ( str_mobile == '' ) {
		alert('请输入'+ str_alertMsg +'手机号！');
		return false;
	}
	
	if ( !MOBILEREG.test(str_mobile) ) {	// 手机号合法性验证
		alert('您输入的'+ str_alertMsg +'手机号不合法，请重新输入！');
		return false;
	}
	return true;
}

/*
* 验证tid是否合法
*/
function fn_validTerminalSn(str_snNum) {
	var SNREG = /^[A-Z0-9]+$/;
	
	if ( str_snNum == '' ) {
		alert('请输入终端序列号！');
		return false;
	}
	if ( !SNREG.test(str_snNum) ) {	// 终端序列号合法性验证
		alert('您输入的终端序列号不合法，请重新输入！');
		return false;
	}
	return true;
}
// 添加遮罩
function fn_lockScreen(str_layerMsg) { 
	var obj_msgcon = $('#layerMsgContent');
	
	$('#maskLayer').css({'display': 'block', 'height': $(window).height()}).data('lock', true);
	$('#msg').css('display', 'block');
	
	if ( str_layerMsg )  {
		obj_msgcon.html(str_layerMsg);
	} else {
		obj_msgcon.html('页面数据正在加载中...');
	}
}

// 去掉遮罩
function fn_unLockScreen() { 
	$('#msg').css('display', 'none');
	$('#maskLayer').css('display', 'none').data('lock', false);
}
/**
* 当用户窗口改变时,地图做相应调整
*/
window.onresize = function () {
	setTimeout (function () {
		//fn_setTitleName();
		
		var f_lock = $('#maskLayer').data('lock');
		
		if ( f_lock ) {
			fn_lockScreen();
		}
	}, 100);
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
        complete: function (XMLHttpRequest, textStatus) { // 页面超时
            var stu = XMLHttpRequest.status;
            if ( stu == 200 && XMLHttpRequest.responseText.search('captchaimg') != -1 ) {
                //window.location.replace('/static/timeout.html'); // redirect to the index.
                return;
            } else if ( stu != 200 ) {
				alert('请求失败，请重新操作！');
				window.location.replace(window.location.href);
			}
        }
	});
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