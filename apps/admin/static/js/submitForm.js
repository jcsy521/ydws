$(function () {	
	// get the login from the cookie 
	if (jQuery.isFunction($.cookie)) {
		var login = decodeURIComponent($.cookie("APPADMIN_N"));
		var loginUser = parent.document.getElementById('loginUser');
		$(loginUser).text('您好，' + login);
	}
});
//formSubmit start end 
function formSubmit(option) {
	var starttime = $('#start_time1').val(),
		endtime = $('#end_time1').val(),
		dailytime = $('#daily_time').val(), // daily
		provs = $('#provincesId').val(),
		str_groups = $('#group').val(),
		mobile = $('#mobile').val();
	if (starttime && endtime) {
		var et = toEpochDate(endtime + ' 23:59:59');
		$('#end_time').val(et);
		$('#start_time').val(toEpochDate(starttime + ' 00:00:00'));
		if (starttime > endtime) {
			alert('开始时间不能大于结束时间！请重新操作。');
			return false;
		}
	}
	// 日报
	if ( option == 'day' ) {
		if ( dailytime ) {
			var et = toEpochDate(dailytime + ' 23:59:59');
			$('#end_time').val(et);
			$('#start_time').val(toEpochDate(dailytime + ' 00:00:00'));
		}
	}
	// 成员订购查询 家长名或者手机号必填
	if ( option == 'search' ) {
		if ( mobile != '' ) {
			return true;
		} else {
			alert('手机号必须填写');
			return false;
		}
	}
}
function fn_validateForm () {
	var $mobile  = $('#mobile'),	 // 手机
		$phone = $('#phone'),	 // 固定电话
		$corporation = $('#corporation'), // 公司名称
		$email = $('#email'),	 // email
		rules = $.validationEngineLanguage.allRules, // 验证规则
		str_mobile = '',
		str_phone = '',
		str_corporation = '',
		str_email = '',
		regex = '',
		alertText = '';
	if ( $mobile ) {
		str_mobile = $.trim($mobile.val());
		regex = eval(rules.mobile.regex);
		alertText = rules.mobile.alertText;
		if ( str_mobile != '' ) {
			if(!regex.test(str_mobile)) {
				alert(alertText);
				$mobile.val('');
				return false;
			}
		}
	}
	if ( $phone ) {
		str_phone = $.trim($phone.val());
		regex = eval(rules.phone.regex);
		alertText = rules.phone.alertText;
		if ( str_phone != '' ) {
			if(!regex.test(str_phone)) {
				alert(alertText);
				$phone.val('');
				return false;
			}
		}
	}
	if ( $corporation ) {
		str_corporation = $.trim($corporation.val());
		regex = eval(rules.sp_char_space.regex);
		alertText = rules.sp_char_space.alertText;
		if ( str_corporation != '' ) {
			if(regex.test(str_corporation)) {
				alert(alertText);
				$corporation.val('');
				return false;
			}
		}
	} 
	if ( $email ) {
		str_email = $.trim($email.val());
		regex = eval(rules.email.regex);
		alertText = rules.email.alertText;
		if ( str_email != '' ) {
			if(!regex.test(str_email)) {
				alert(alertText);
				$email.val('');
				return false;
			}
		}
	}
	return true;
}
//admin submit
function adminSubmit(is_self) {
    if (is_self) {
      return fn_validateForm();
    } else { 
		if ( fn_validateForm() ) {
			var privs = '';
			var cities = '';
			$('#ulCheckbox li >input').each(function () {
				if ($(this).attr('checked') == true) {
					privs = privs + $(this).val() + ","
				} 
			});
			privs = privs.substr(0, privs.length - 1);
			// 城市 值
			cities = $('#citiesNames').val();
			if (privs == '') {
				alert('必须为用户选择一项权限！');
				return false;
			}
			if (cities != '') {
				return true;
			} else {
				alert('请选择您要操作的市。');
				return false;
			}
		} else {
			return false;
		}
	}
}
// timestamp monthly 
function formSubmit2() {
	var year = $('#yeartemp').val(),
		month = $('#monthtemp').val(),
		obj_data = new Date(),
		currentMonth = obj_data.getMonth()+1,
		currentYear = obj_data.getFullYear();
	if ( year > currentYear ) {
		alert('数据还没有统计。您可以查询' + currentYear + '年' + currentMonth + '月之前的数据。');
		return false;
	} else if ( year == currentYear ) {
		if ( month >= currentMonth ) {
			alert('数据还没有统计。您可以查询' + currentMonth+'月之前的数据。');
			return false;
		}
	}
	if (year && month) {
		$('#timestamp').val(toEpochDate((year + '-' + month + '-01') + ' 00:00:00'));
	}
}
/**
    * go back history page
*/
function fn_GoBack() {
    var parentURL = parent.document.URL; // http://drone-005:6400 or http://drone-005:6400#
    var dref = document.referrer;
    if ((parentURL != dref) && (parentURL != dref+'#')) {
        window.location.replace(document.referrer);
    } else {
        parent.location.replace('/');
    }
}

// 获取当月的最后一天
function fn_getLastDayOfCurrentMonth() {
	var date = new Date(), year = date.getFullYear(), month = date.getMonth();
	var nextDate = new Date(year, month+1, 1); // 下个月的第一天
	return new Date(nextDate.getTime()-1000*60*60*24).getDate();
}