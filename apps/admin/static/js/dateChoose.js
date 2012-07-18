$(function() {
	fn_InitChooseDate();
});
function toTodayDate() { // 返回当天的日期的UTC表示:例如2010-11-05 只判断日期
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
function toHumanDate(myEpoch, flag) { // 将UTC时间转为正常时区时间
	if ( !myEpoch ) {
		return '未知时间';
	}
	var myDate = new Date(Number(myEpoch));
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
	if (flag == 'no') {
		return year + '-' + month + '-' + day;//2010-09-10 z
	} else {
		return year + '-' + month + '-' + day + ' ' + hours + ':' + min + ':' + seconds;
	}
}
function toEpochDate(dateString) { // 将正常时区时间转为UTC时间
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
		var myEpoch = myDate.getTime();
		return myEpoch;
	}
}
function fn_InitChooseDate() {
    var startTemp = $('#start_temp').val();
	var endTemp = $('#end_temp').val();
	var dateTemp = $('#date_temp').val();
	
	//设置开始时间
	if (startTemp == 'start' || startTemp == '') {
		$('#start_time1').val(toTodayDate()); 
	} else if ( startTemp == 'user_start' ) { // 集团订购查询 默认开始时间显示月初
		$('#start_time1').val(getFirstDayOfMonth());
	} else if ( startTemp == 'daily_time' ) { // 日报
		$('#daily_time').val(getYesterday());
	} else {
		$('#start_time1').val(toHumanDate(startTemp, 'no'));
		$('#daily_time').val(toHumanDate(startTemp, 'no')); // 日报
	}
	//设置结束时间
	if (endTemp == 'end' || endTemp == '') {
		$('#end_time1').val(toTodayDate()); 
	} else {
		$('#end_time1').val(toHumanDate(endTemp, 'no'));
	}
	//对月份进行设置
	if (dateTemp == 'monthly') {
		var myDate = new Date();
		var year = myDate.getFullYear();
		var month = (myDate.getMonth()); // 当前月 0-11 
		if (month < 10) {
		    month = '0' + month;
		}
		$('#yeartemp').attr('value', year);
		$('#monthtemp').attr('value', month);
	} else {
		var myDate = new Date(Number(dateTemp));
		var year = myDate.getFullYear();
		var month = myDate.getMonth() + 1;
		if (month < 10) {
			month = '0' + month;
		}
		$('#yeartemp').attr('value', year);
		$('#monthtemp').attr('value', month);
	}
}
// test: 201203071708255231
function toDateIntToString(str_time) { // 返回当天的日期的UTC表示:例如2010-11-05 只判断日期
	var str_time = str_time.toString(), 
		year = str_time.substr(0, 4),
		month = str_time.substr(4, 2),
		day = str_time.substr(6, 2),
		hours = str_time.substr(8, 2),
		min = str_time.substr(10, 2),
		seconds = str_time.substr(12, 2);
	
	return year + '-' + month + '-' + day + ' ' + hours + ':' + min + ':' + seconds;
}
// test: 2012-06-01  2012-05-01
function getFirstDayOfMonth() {
	var date = new Date(),
		year = date.getFullYear(),
		month = date.getMonth() +1,
		day = '01';
	if ( month < 10 ) {
		month = '0' + month;
	}
	return year + '-' + month + '-' + day;
}
// 获取昨天时间
function getYesterday() {
	var dd = new Date();
	dd.setDate(dd.getDate()-1);	
	var year = dd.getFullYear(),
        month = dd.getMonth()+1, //获取当前月份的日期
		day = dd.getDate();
	if ( month < 10 ) {
		month = '0' + month;
	} 
	if ( day < 10) {
		day = '0' + day;
	}
    return year+"-"+month+"-"+day;
}