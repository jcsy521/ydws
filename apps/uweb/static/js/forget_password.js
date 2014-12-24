var obj_updateTimeInterval =null;	// 找回密码倒数计时
$(function(){
	$('#jNotifyMessage').css('top', 50);
	$('#mobile').val('').keyup(function(e) {
	
		if ( $('#flashTimeText').html() != '' ) {	// 如果小于60 秒 不能发送
			$('#btnGetCaptcha').attr('disabled',true);
		} else {
			$('#btnGetCaptcha').removeAttr('disabled');
		}
	});
	$('#pwd_captcha').val('');
	// 找回密码获取验证码
	$('#btnGetCaptcha').click(function() {
		var str_val = $.trim($('#mobile').val()),
			str_captchaImgVal = $.trim($('#txt_imgCaptcha').val()),
			obj_param = {'mobile': str_val, 'captcha_psd': str_captchaImgVal},
			str_updateTime = $('#flashTimeText').html(),
			str_userType = $('#userRoleType').val(),
			str_url = PWD_CAPCHA_URL;
			
		if ( str_userType == 'enterprise' ) {
			str_url = CORPPWD_CAPCHA_URL;
		}
		if ( str_updateTime != '' && str_updateTime != 0 ) {
			dlf.fn_jNotifyMessage('请稍后获取。', 'message', false, 3000);
			return;
		}
		
		//验证图形验证码
		if ( str_captchaImgVal == '' ) {
			dlf.fn_jNotifyMessage('图形验证码不能为空。', 'message', false, 3000);
			return;
		}
		if ( str_captchaImgVal.length < 4 ) {
			dlf.fn_jNotifyMessage('请输入正确的图形验证码', 'message', false, 3000);
			return;
		}
			
		
		if ( str_val == '' || str_val == null ) {	// 车主手机号不为空验证格式
			dlf.fn_jNotifyMessage('手机号码不能为空。', 'message', false, 3000);
			return;
		} else {
			var reg = MOBILEREG;
				
			if ( !reg.test(str_val) ) {	// 车主手机号合法性验证
				dlf.fn_jNotifyMessage('请填写正确的手机号。', 'message', false, 3000);
				return;
			}
			$.post_(str_url, JSON.stringify(obj_param) , function(data) {
				if ( data.status == 0 ) { 
					str_msg = '您的验证码已发送成功，请注意查收。';
					fn_resetUpdateTime();	// 重新读秒操作
					
					$('#btnGetCaptcha').attr('disabled', 'disabled');
					$('#btnGetPwd').removeAttr('disabled');
				} else {
					str_msg = data.message;
				}
				dlf.fn_jNotifyMessage(str_msg, 'message', false, 3000);
			}, 
			function(XMLHttpRequest, textStatus, errorThrown) {
				//dlf.fn_serverError(XMLHttpRequest);
			});
		}
	}).attr('disabled',true);
	
	/**
	* 找回密码的相关事件绑定
	*/
	$('#btnGetPwd').click(function() {
		var str_val = $('#mobile').val(),
			str_captchaVal = $('#pwd_captcha').val(),
			str_captchaImgVal = $('#txt_imgCaptcha').val(),
			str_msg = '',
			obj_param = {'mobile': str_val, 'captcha': str_captchaVal},
			str_userType = $('#userRoleType').val(),
			str_url = PWD_URL;
			
		if ( str_userType == 'enterprise' ) {
			str_url = CORPPWD_URL;
		}
		//验证手机号
		if ( str_val == '' || str_val == null ) {	// 车主手机号不为空验证格式
			dlf.fn_jNotifyMessage('手机号码不能为空。', 'message', false, 3000);
			return;
		} else {
			var reg = MOBILEREG,
				n_seconds = parseInt($('#flashTimeText').html());
				
			if ( !reg.test(str_val) ) {	// 车主手机号合法性验证
				dlf.fn_jNotifyMessage('请填写正确的手机号。', 'message', false, 3000);
				return;
			}
			//验证验证码
			if ( str_captchaVal == '' ) {
				dlf.fn_jNotifyMessage('验证码不能为空。', 'message', false, 3000);
				return;
			}
			if ( n_seconds < 60 ) {	// 如果小于60 秒 不能发送
				$('#btnGetCaptcha').attr('disabled',true);
			} else {
				$('#btnGetCaptcha').removeAttr('disabled');
			}
			$.post_(str_url, JSON.stringify(obj_param) , function(data) {
				if ( data.status == 0 ) { 
					
					$('#mobile, #pwd_captcha, #txt_imgCaptcha').val('');
					$('#captchaimg').click();
					
					$('#btnGetPwd').attr('disabled', 'disabled');
					str_msg = '您的密码已发送成功，请注意查收。';
				} else {
					str_msg = data.message;
				}
				dlf.fn_jNotifyMessage(str_msg, 'message', false, 3000);
			}, 
			function(XMLHttpRequest, textStatus, errorThrown) {
				//dlf.fn_serverError(XMLHttpRequest);
			});
		}
	});
	
	/**
	* 验证码图形及hash值得设置
	*/
	var obj_captchaImg= $('#captchaimg');
	
	obj_captchaImg.click(function () {
		fn_getCaptcha($(this));
	});
	$('#captchaimgRp').click(function () {
		fn_getCaptcha(obj_captchaImg);
	});
	fn_getCaptcha(obj_captchaImg);
});

/**
* 验证码图形及hash值得设置
*/
function fn_getCaptcha($obj) {
	$obj.attr('src', '/captchapsd?nocache=' + Math.random()).load(function () {
		//$('#captchahash').val($.cookie('captchahash'));
	});
}

/**
* 找回密码的读秒操作
*/
function fn_updateTime() {
	obj_updateTimeInterval = setInterval(function() {
		var obj_updateTime = $('#flashTimeText'),
			str_updateTime = obj_updateTime.html();
		if ( parseInt(str_updateTime) == 0 ) {
			dlf.fn_clearInterval(obj_updateTimeInterval);
			obj_updateTime.html('');
			$('#seconds').hide();
			$('#btnGetCaptcha').removeAttr('disabled');
		} else {
			obj_updateTime.html(parseInt(str_updateTime)-1);
		}
	}, 1000);
}

/** 
* 重新启动读秒操作
*/
function fn_resetUpdateTime() {
	dlf.fn_clearInterval(obj_updateTimeInterval);
	$('#flashTimeText').html(60);
	$('#seconds').show();
	fn_updateTime();
}