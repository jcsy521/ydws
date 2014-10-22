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
