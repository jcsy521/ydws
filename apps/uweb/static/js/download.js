$(function () {
	var obj_smsWrapper = $('#smsUploadWrapper'), 
		obj_smsLayer = $('#downloadLayer');
	
	// 为短信下载添加相应事件
	$('#smsDown').click(function() {
		fn_showSmsWrapper();
	});
	// 点击页面的X关掉页面
	$('.j_close').click(function (event) {
		obj_smsWrapper.hide();
		obj_smsLayer.removeClass().css({'display': 'none','height': '0px'});
	});
	// 验证码
	var $imgElem = $('#smsCaptchaimg'), 
		obj_sendBtn = $('#sendSms'), 
		obj_captcha = $('#captcha_sms');
	
	$imgElem.click(function () {
		fn_changeSmsCaptcha($(this));
	});
	fn_changeSmsCaptcha($imgElem);
	obj_captcha.val('').keyup(function() {
		obj_sendBtn.removeClass('btnDisabled').unbind('click').bind('click', fn_sendBtn);
	});
});
// 发送短信
function fn_sendBtn() {
	var str_mobile = $('#txtmobile').val(), 
		obj_captcha = $('#captcha_sms'), 
		obj_sendBtn = $('#sendSms'), 
		str_captchaText = obj_captcha.val(), 
		str_captchaImg = $('#captchahash_sms').val(),
		obj_msg = $('.j_smsMsg');
	// 验证格式
	if ( str_mobile == '' || str_mobile == null ) {
		obj_msg.html('请输入手机号码！');
		return;
	} else {
		// 验证手机号
		var reg = /^(13[0-9]|15[7-9]|15[0-3]|15[56]|18[023789]|147)[0-9]{8}$/;
		if ( !reg.test(str_mobile) ) {
			obj_msg.html('请输入合法的手机号码！');
			return;
		} else {
			obj_msg.html('');
			if ( str_captchaText == '' ) {
				obj_msg.html('请输入验证码！');
			} else {
				obj_postData = {'category': 2, 'mobile': str_mobile, 'captcha_sms': str_captchaText, 'captchahash_sms': str_captchaImg};
				$.post('/downloadsms', JSON.stringify(obj_postData), function(data){
					var obj_msg = $('.j_smsMsg');
					if ( data.status == 0 ) {
						obj_sendBtn.addClass('btnDisabled').unbind('click');
						obj_captcha.val('');
						obj_msg.html('<font color="green">短信发送成功！</font>');
					} else {
						obj_msg.html(data.message);
					}
				});
			}
		}
	}
}

// 获取后台验证码
function fn_changeSmsCaptcha($obj) {
	$obj.attr('src', '/captchasms?nocache=' + Math.random()).load(function () {
		$('#captchahash_sms').val($.cookie('captchahash_sms'));
	});
}
// 显示短信提示框 
function fn_showSmsWrapper() {
	var obj_smsWrapper = $('#smsUploadWrapper'), 
		obj_smsLayer = $('#downloadLayer');
	
	fn_changeSmsCaptcha($('#smsCaptchaimg'));
	obj_smsWrapper.show();
	obj_smsLayer.addClass('iLayer').css({
		'display': 'block',
		'height': $(window).height()+'px'
	});
	$('#sendSms').removeClass('btnDisabled').unbind('click').bind('click', fn_sendBtn);
	$('.j_smsMsg').html('');
}