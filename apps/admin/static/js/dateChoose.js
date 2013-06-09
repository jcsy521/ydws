$(function() {
	fn_InitChooseDate();
	
	$('#reportThead th').removeAttr('style');
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
		var myEpoch = myDate.getTime() / 1000;
		return myEpoch;
	}
}
function fn_InitChooseDate() {
    var startTemp = $('#start_temp').val(),
		endTemp = $('#end_temp').val(),
		dateTemp = $('#date_temp').val(), 
		dateTemp2 = $('#date_temp2').val(),
		str_dateRole = $('#date_role').val(),
		myDate =  new Date()/1000, 
		obj_startTime = $('#start_time1'),
		obj_dailyTime = $('#daily_time'),
		obj_endTime = $('#end_time1'),
		str_yesterday = getYesterday(),
		str_today = toTodayDate(),
		str_firstDayOfMonth = getFirstDayOfMonth(),
		str_year =  toHumanDate(myDate, 'year'),
		str_month = toHumanDate(myDate, 'month');

	//设置开始时间
	if (startTemp == 'start' || startTemp == '') {
		obj_startTime.val(str_today); 
	} else if ( startTemp == 'user_start' ) { // 地市用户统计 默认开始时间显示月初
		obj_startTime.val(str_firstDayOfMonth);
	} else if ( startTemp == 'daily' ) { // 日报
		obj_dailyTime.val(str_today);
	} else if ( startTemp == 'business_begin' || startTemp == '0' ) { // 个人用户查询,集团查询
		obj_startTime.val(str_firstDayOfMonth); 
	} else if ( startTemp == 'userReport_start' ) {	// 个人用户统计、集团用户统计、所有用户统计
		obj_startTime.val(str_firstDayOfMonth); 	//  
	} else {
		obj_startTime.val(toHumanDate(startTemp, 'no')); 	//  
		obj_dailyTime.val(toHumanDate(startTemp, 'no')); // 日报 
		$('#begintime1').val(str_today);	// create business 
	}
	//设置结束时间
	if (endTemp == 'end' || endTemp == '') {
		obj_endTime.val(str_today); 
	} else if ( endTemp == 'business_end' || endTemp == '0' ) {// 个人用户查询,集团查询
		obj_endTime.val(str_today); 
	} else if ( endTemp == 'userReport_end' ) {
		obj_endTime.val(str_yesterday);
	} else {
		obj_endTime.val(toHumanDate(endTemp, 'no')); 	
		$('#endtime1').val(fn_getNextYearToday());	// create business 
	}
	//对月份进行设置
	var obj_year = $('#yeartemp'),
		obj_month = $('#monthtemp'), 
		obj_chart = $('#chartData');
	
	obj_chart.hide(); 
	if ( str_dateRole == 'monthly' ) { 
		if (dateTemp == 'monthly') {
			obj_year.html(fn_createYearOrMonthOptions('year')).val(str_year);
			obj_month.html(fn_createYearOrMonthOptions('month')).val(str_month);
		} else { 
			if ( str_year != dateTemp ) {
				obj_month.html(fn_createYearOrMonthOptions('month', 'year'));
			} else {
				obj_month.html(fn_createYearOrMonthOptions('month'));
			}
			obj_year.html(fn_createYearOrMonthOptions('year')).attr('value', dateTemp);
			obj_month.attr('value', dateTemp2);
			// 对查询到的数据进行统计初始化
			fn_initChartData();
		}
		obj_year.unbind('change').change(function() {
			var str_selectData = $(this).val();
			
			if ( str_year != str_selectData ) {
				obj_month.html(fn_createYearOrMonthOptions('month', 'year')).attr('value', '1');
			} else {
				obj_month.html(fn_createYearOrMonthOptions('month'));
			}
		});
	} else if ( str_dateRole == 'yearly' ) { 
		//  对年份进行设置
		if (dateTemp == 'yearly') {
			var str_year =  toHumanDate(myDate, 'year');
			
			obj_year.html(fn_createYearOrMonthOptions('year')).val(str_year);
		} else {
			obj_year.html(fn_createYearOrMonthOptions('year')).attr('value', dateTemp);
			// 对查询到的数据进行统计初始化
			fn_initChartData();
		}
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
// get today of  next year 
function fn_getNextYearToday() {
	var myDate = new Date(),
		year = myDate.getFullYear()+1,
		temp_month = myDate.getMonth()+1,
		month = temp_month < 10 ? '0' + temp_month : temp_month,
		temp_day = myDate.getDate(),
		day = temp_day < 10 ? '0' + temp_day : temp_day;
	return year+'-'+month+'-'+day;
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
// 获取当月的最后一天
function fn_getLastDayOfCurrentMonth() {
	var date = new Date(), year = date.getFullYear(), month = date.getMonth();
	var nextDate = new Date(year, month+1, 1); // 下个月的第一天
	return new Date(nextDate.getTime()-1000*60*60*24).getDate();
}

/** 
* kjj 2013-06-03 create
* 秒转化成 xx天xx时xx秒
*/
function fn_changeTimestampToString(n_timestamp) {
	var n_tempMinute = Math.round(n_timestamp/60),
		n_minute = n_tempMinute,
		n_hour = 0,
		n_tempHour = 0,
		n_day = 0,
		str_time = '';
		
	if ( n_tempMinute >= 60 ) {
		n_minute = n_tempMinute%60;
		n_hour = Math.floor(n_tempMinute/60);
		
		if ( n_hour >= 24 ) {
			n_tempHour = n_hour;
			n_hour = n_hour%24;
			n_day = Math.floor(n_tempHour/24);
			
			str_time += n_day + '天 ';	
		}
		str_time += n_hour + '时';	
	}
	str_time += n_minute + '分 ';
	return str_time;
}