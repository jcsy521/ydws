$(function() {
	$.ajaxSetup({ cache: false }); // 不保存缓存
	
	var n_time = 60, 
		MOBILEREG =  /^(\+86){0,1}1(3[0-9]|5[012356789]|8[023456789]|47)\d{8}$/;	// 手机号正则表达;
		
	 // 数据清空 添加获取焦点失去焦点样式
	$('#registerForm input[type=text]').val('').unbind('focus, blur').bind('focus', function() {
		$(this).parent().addClass('focus');
	}).bind('blur', function() {
		$(this).parent().removeClass('focus');
	});
	$('#txt_tmobile').unbind('blur').bind('blur', function() {
		var str_tmobile = $('#txt_tmobile').val(),
			n_valLength = str_tmobile.length;
		
		if ( n_valLength > 14 || n_valLength < 11 ) {
			dlf.fn_jNotifyMessage('定位器手机号输入不合法，请重新输入！', 'error', false, 3000);
			return;
		} else {
			if ( !MOBILEREG.test(str_tmobile) ) {	// 手机号合法性验证
				dlf.fn_jNotifyMessage('定位器手机号格式不正确，请重新输入！', 'error', false, 3000);
				return;
			}
		}
		$.get_('/checktmobile' + '/' + str_tmobile, '', function(data){
			if ( data.status != 0 ) {
				dlf.fn_jNotifyMessage(data.message, 'error', false, 5000);
				$('#txt_tmobile').data({'errormsg': data.message, 'isvalid': false});
				return;
			}
			$('#txt_tmobile').data({'isvalid': true});
			dlf.fn_closeJNotifyMsg('#jNotifyMessage');
		}, 
		function (XMLHttpRequest, textStatus, errorThrown) {
			//dlf.fn_serverError(XMLHttpRequest);
		});
	});
	$.formValidator.initConfig({
		formID: 'registerForm', //指定from的ID 编号
		debug: true, // 指定调试模式,不提交form
		wideWord: false, // 一个汉字当一个字节
		submitButtonID: 'btn_register', // 指定本form的submit按钮
		onError: function(msg, ea) {
			dlf.fn_jNotifyMessage(msg, 'error', false, 4000);
			$(ea).addClass('borderRed');
		}, 
		onSuccess: function() { 
			var str_mobile = $('#txt_umobile').val(),
				str_tmobile = $('#txt_tmobile').val(),
				str_captcha = $('#captcha').val(),
				str_Imgcaptcha = $('#txt_imgCaptcha').val(),
				str_url = '/register',
				obj_param = {'umobile': str_mobile, 'tmobile': str_tmobile, 'captcha': str_captcha};
			
			$.post_(str_url, JSON.stringify(obj_param), function(data) {
				if ( data.status == 0 ) {
					/*dlf.fn_jNotifyMessage('注册信息已提交成功，请稍后注意查收短信。', 'message', false, 3000);
					window.setTimeout(function() {
						location.href = '/login';
					}, 3000);
					return;*/
					$('#registerPanel').hide();
					$('.j_tips').hide();
					$('#register_success').show();
					window.setInterval(function() {
						var obj_intervalTip = $('.j_interval'),
							n_oldInterval = parseInt(obj_intervalTip.html());
							
						if ( n_oldInterval == 1 ) {
							location.href = '/login';
						} else {
							n_oldInterval--;
							obj_intervalTip.html(n_oldInterval);
						}
					}, 1000);
					return;
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
					return;
				}
			}, 
			function(XMLHttpRequest, textStatus, errorThrown) {
				//dlf.fn_serverError(XMLHttpRequest);
			});
		}
	});
		
	// 获取验证码
	$('#btnCaptcha').unbind('click').bind('click', function() {
		var obj_mobile = $('#txt_umobile'),
			str_tmobile = $.trim($('#txt_tmobile').val()),
			obj_captchaBtn = $('#btnCaptcha'),
			str_mobile = $.trim(obj_mobile.val()),
			obj_captcha = $('#captcha'),
			b_flag  = $('#mobileTip .onError').is(":visible"),
			b_tmobile = $('#txt_tmobile').data('isvalid');
			n_seconds = parseInt($('#flashTimeText').html()),
			str_Imgcaptcha = $.trim($('#txt_imgCaptcha').val());
		
		obj_mobile.parent().addClass('focus');
		obj_mobile.focus();
		
		if ( n_seconds < 60 ) {	// 如果小于60 秒 不能发送
			obj_captchaBtn.attr('disabled',true);
			return;
		} else {
			obj_captchaBtn.removeAttr('disabled');
		}		
		
		if ( str_Imgcaptcha == '' ) {
			dlf.fn_jNotifyMessage('请输入图形验证码', 'error', false, 3000);
			$('#txt_imgCaptcha').focus();
			return;
		} else if ( str_Imgcaptcha.length < 4 ) {
			dlf.fn_jNotifyMessage('请输入正确的图形验证码', 'error', false, 3000);
			$('#txt_imgCaptcha').focus();
			return;
		}		
		
		if ( str_mobile == '' ) {  
			dlf.fn_jNotifyMessage('请输入用户手机号！', 'error', false, 3000);
			obj_mobile.focus();
			return;
		} else if ( !MOBILEREG.test(str_mobile) ) {	// 手机号合法性验证
			dlf.fn_jNotifyMessage('您输入的号码不合法，请重新输入！', 'error', false, 3000);
			obj_mobile.focus();
			return;
		}
		
		if ( str_tmobile.length > 14 || str_tmobile.length < 11 ) {
			dlf.fn_jNotifyMessage('定位器手机号输入不合法，请重新输入！', 'error', false, 3000);
			$('#txt_tmobile').focus();
			return;
		} else if ( !MOBILEREG.test(str_tmobile) ) {	// 手机号合法性验证
			dlf.fn_jNotifyMessage('定位器手机号格式不正确，请重新输入！', 'error', false, 3000);
			$('#txt_tmobile').focus();
			return;		
		}else if ( !b_tmobile ) {			
			dlf.fn_jNotifyMessage($('#txt_tmobile').data('errormsg'), 'error', false, 3000);
			$('#txt_tmobile').focus();
			return;
		}
		
		$.get_('/register?umobile='+str_mobile+'&tmobile='+str_tmobile+'&captcha_img='+str_Imgcaptcha, '', function(data) {
			if ( data.status == 0 ) {
				//  倒计时1分钟 同时 按钮不可用
				dlf.fn_jNotifyMessage('验证码发送到您的手机，请在5分钟内激活。', 'message', false, 5000);
				fn_resetUpdateTime();	// 重新读秒操作
				$('#btnCaptcha').attr('disabled',true);
				obj_captcha.parent().addClass('focus');
				obj_captcha.focus();
			} else {
				if ( data.status == 203 ) {
					$('#txt_imgCaptcha').focus();
				}
				dlf.fn_jNotifyMessage(data.message, 'error', false, 3000);
			}
		}, 
		function (XMLHttpRequest, textStatus, errorThrown) {
			//dlf.fn_serverError(XMLHttpRequest);
		});
	}).removeAttr('disabled');
	
	$('#txt_umobile').formValidator().inputValidator({min: 1, onError: '请输入用户手机号！'}).regexValidator({regExp: 'mobile', dataType: 'enum', onError:'用户手机号格式不正确，请重新输入！'});
	
	$('#txt_tmobile').formValidator().inputValidator({min: 1, onError: '请输入定位器手机号！'}).regexValidator({regExp: 'mobile', dataType: 'enum', onError:'定位器手机号格式不正确，请重新输入！'});
	
	$('#captcha').formValidator().inputValidator({min: 1, onError: '请输入验证码！'});

	$('#serviceTerms').formValidator().inputValidator({min: 1, onError: '请阅读并同意遵守服务条款！'}); 
	
	/**
	* 验证码图片及hash值得设置
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
* 验证码图片及hash值得设置
*/
function fn_getCaptcha($obj) {
	$obj.attr('src', '/captchaimage?nocache=' + Math.random()).load(function () {
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
			$('#btnCaptcha').removeAttr('disabled');
		} else {
			obj_updateTime.html(parseInt(str_updateTime)-1);
		}
	}, 1000);
}
/** 
* 重新启动读秒操作
*/
var obj_updateTimeInterval =null;	// 获取验证码倒数计时
function fn_resetUpdateTime() {
	dlf.fn_clearInterval(obj_updateTimeInterval);
	$('#flashTimeText').html(60);
	$('#seconds').show();
	fn_updateTime();
}