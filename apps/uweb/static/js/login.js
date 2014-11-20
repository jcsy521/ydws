/**
* 登录、忘记密码功能
*/
$(function(){
	$.ajaxSetup({ cache: false }); // 不保存缓存
	var str_host = window.location.host,
		obj_captchaImg= $('#captchaimg');
	
	if ( str_host == 'ajt.zhydgps.com' || str_host == 'ajt.ichebao.net' ) { 
		document.title='安捷通--登录';
		$('.top').css('background-image', 'url("/static/images/loginBg_ajt.png")');
		$('#font_tipContent').html('安捷通');
		$('#loginHeader_logo').css('background-image', 'url("/static/images/login/logo_ajt.png")');
	}
	
	/**
	* input 的change事件 不能输入汉字
	*/
	$('.j_replace').unbind('change').bind('change', function() {
		var obj_this = $(this),
			str_val = obj_this.val();
			
		obj_this.val(str_val.replace(/[^\w|chun]/g,''));
	});
	
	/**
	* 验证码图片及hash值得设置
	*/
	obj_captchaImg.click(function () {
		fn_getCaptcha($(this));
	});
	$('#captchaimgRp').click(function () {
		fn_getCaptcha(obj_captchaImg);
	});
	fn_getCaptcha(obj_captchaImg);
	
	// 体验
	$('#login_ty').click(function(e) {
		$('#login_tyForm').submit();
	});	
	
	$('#loginBtn').unbind('click keyup').click(function(e) {
		$('#loginForm').submit();
	}).keyup(function(e) {
		if ( e.keyCode == 13 ) {
			$('#loginForm').submit();
		}
	});
	if ( $('#userRoleType').val() == 'individual' ) {	 
		$('#login_enterprise').removeClass('current');
		$('#login_individual').addClass('current');
	} else {
		$('#login_enterprise').addClass('current');
		$('#login_individual').removeClass('current');
		$('#loginHeader_register, #loginHeader_roleLine, #login_ty, #getPwd').hide();
		$('#corpGetPwd').show();
	}
	
	$('#login_individual').unbind('click').click(function(e) {
		$('#login_enterprise').removeClass('current');
		$(this).addClass('current');
		$('#loginHeader_register, #loginHeader_roleLine, #login_ty, #getPwd').show();
		$('#corpGetPwd').hide();
		$('#userRoleType').val('individual');
	});
	$('#login_enterprise').unbind('click').click(function(e) {
		$('#login_individual').removeClass('current');
		$(this).addClass('current');
		$('#loginHeader_register, #loginHeader_roleLine, #login_ty, #getPwd').hide();
		$('#corpGetPwd').show();
		$('#userRoleType').val('enterprise');
	});
	//登录 页面部分验证
	$('#loginBtn').data('isvalid', true);
	$('#login_username').unbind('blur').blur(function(e) {
		var str_loginUserName = $.trim($(this).val()),
			MOBILEREG = /^(\+86){0,1}1(3[0-9]|5[012356789]|8[023456789]|47)\d{8}$/;
		
		if ( str_loginUserName == '' || MOBILEREG.test(str_loginUserName) ) {	// 手机号合法性验证
			$('.login_usernameMsgPanel').hide();
			$('#login_usernameErrorMsg').html('');
			$('#loginBtn').data('isvalid', true);
		} else {
			$('.login_usernameMsgPanel').show();
			$('#login_usernameErrorMsg').html('请输入规范的手机号码');
			$('#loginSubmitErrorMsgPanel, #loginCaptchaErrorMsgPanel').hide();
			$('#loginBtn').data('isvalid', false);
			$('.login_msgPanel').hide();
			$('.login_errorMsg').html('');
		}
	});
	
	
	
});

/**
* 验证码图片及hash值得设置
*/
function fn_getCaptcha($obj) {
	$obj.attr('src', '/captcha?nocache=' + Math.random()).load(function () {
		//$('#captchahash').val($.cookie('captchahash'));
	});
}

/**
* 对登录字段处理
*/
function fn_validLogin() {
	var str_loginName = $.trim($('#login_username').val()),
		str_loginPwd = $.trim($('#login_pwd').val()),
		str_loginCaptcha = $.trim($('#login_captcha').val()),
		str_randomStr = fn_createRandomStr(128);
	
	if ( !$('#loginBtn').data('isvalid') ) {
		return false;
	}
	
	if ( str_loginName == '' ) {
		$('#loginSubmitErrorMsgPanel').show();
		$('#loginSubmitErrorMsg').html('登录名不能为空');
		$('#login_captcha').val('');
		$('#loginCaptchaErrorMsgPanel').hide();
		return false;
	}
	if ( str_loginPwd == '' ) {
		$('#loginSubmitErrorMsgPanel').show();
		$('#loginSubmitErrorMsg').html('密码不能为空');
		$('#login_captcha').val('');
		$('#loginCaptchaErrorMsgPanel').hide();
		return false;
	}
	if ( str_loginCaptcha == '' ) {
		$('#loginSubmitErrorMsgPanel').show();
		$('#loginSubmitErrorMsg').html('请输入验证码');
		$('#loginCaptchaErrorMsgPanel').hide();
		return false;
	}
	$('#loginSubmitErrorMsgPanel').hide();	
	
	$('#loginHidden_username').val(base64encode(utf16to8(str_randomStr+str_loginName)));
	$('#loginHidden_pwd').val(base64encode(utf16to8(str_randomStr+str_loginPwd)));
	$('#loginHidden_captcha').val(base64encode(utf16to8(str_randomStr+str_loginCaptcha)));
	return true;
}

/**
* 生成一个随机数
*/

function fn_createRandomStr(n_randomNum) {
	var str_baseCode = '23456789ABCDEFGHJKMNPQRSTUVWXYZ',
		str_returncode = '';
	
	for ( var i = 0; i< n_randomNum; i++ ) {
		var n_tempRandomNum = Math.random()*30+1,
			str_tempCode = str_baseCode.substr(n_tempRandomNum, 1);
		
		str_returncode += str_tempCode;
	}
	return str_returncode;
}
