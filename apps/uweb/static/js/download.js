/**
* 短信下载功能
*/
$(function () {
	var obj_smsWrapper = $('#smsUploadWrapper'),	// 短信下载diaolog
		obj_smsLayer = $('#downloadLayer');		// 短信下载遮罩层
	
	$('#smsDown').click(function() {	// 为短信下载添加相应事件
		fn_showSmsWrapper();
	});
	$('.j_close').click(function (event) {	// 点击页面的X关掉页面
		obj_smsWrapper.hide();
		obj_smsLayer.removeClass().css({'display': 'none','height': '0px'});
	});
	
	var obj_smsCaptchaimg = $('#smsCaptchaimg'), // 验证码图片
		obj_sendBtn = $('#sendSms'), 	// 发送短信按钮
		obj_captcha = $('#captcha_sms');	// 验证码输入框
	
	obj_smsCaptchaimg.click(function () {	// 验证码图片点击事件
		fn_changeSmsCaptcha($(this));
	});
	fn_changeSmsCaptcha(obj_smsCaptchaimg);	// 获取验证码
	obj_captcha.val('').keyup(function() {	// 设置验证码输入框与发送短信按钮的事件
		obj_sendBtn.removeClass('btnDisabled').unbind('click').bind('click', fn_sendBtn);
	});
});

/**
* 发送短信
*/
function fn_sendBtn() {
	var str_mobile = $('#txtmobile').val(), 
		obj_captcha = $('#captcha_sms'), 
		obj_sendBtn = $('#sendSms'), 
		str_captchaText = obj_captcha.val(), 
		str_captchaImg = $('#captchahash_sms').val(),
		obj_msg = $('.j_smsMsg');
		
	if ( str_mobile == '' || str_mobile == null ) {	// 验证手机号的输入格式
		obj_msg.html('请输入手机号码。');
		return;
	} else {
		var mobileReg = MOBILEREG;	// 手机号正则表达式
		if ( !mobileReg.test(str_mobile) ) {	// 验证手机号合法性
			obj_msg.html('请输入合法的手机号码。');
			return;
		} else {
			obj_msg.html('');
			if ( str_captchaText == '' ) {
				obj_msg.html('请输入验证码！');
			} else {
				obj_postData = {'category': 2, 'mobile': str_mobile, 'captcha_sms': str_captchaText, 'captchahash_sms': str_captchaImg};	// 发送到后台的数据
				$.post('/downloadsms', JSON.stringify(obj_postData), function(data){
					if ( data.status == 0 ) {	// 发送成功后发送按钮操作状态不可用，验证码清空
						obj_sendBtn.addClass('btnDisabled').unbind('click');
						obj_captcha.val('');
						obj_msg.html('<font color="green">短信发送成功。</font>');
					} else {
						obj_msg.html(data.message);
					}
				});
			}
		}
	}
}

/**
* 获取后台验证码图片及hash值
* obj_captchaImg: 显示验证码图片
*/
function fn_changeSmsCaptcha(obj_captchaImg) {
	obj_captchaImg.attr('src', '/captchasms?nocache=' + Math.random()).load(function () {
		$('#captchahash_sms').val($.cookie('captchahash_sms'));	// 验证码图片的hash值
	});
}

/**
* 显示短信提示框 
*/
function fn_showSmsWrapper() {
	var obj_smsWrapper = $('#smsUploadWrapper'), 
		obj_smsLayer = $('#downloadLayer'),
		n_clientHeight = document.documentElement.clientHeight,
		n_scrollHeight = document.documentElement.scrollHeight,
		n_layerHeight = n_clientHeight > n_scrollHeight ? n_clientHeight : n_scrollHeight;
	
	fn_changeSmsCaptcha($('#smsCaptchaimg'));	// 获取后台验证码
	obj_smsWrapper.show();	// 显示短信下载dialog
	obj_smsLayer.addClass('iLayer').css({	// 添加遮罩层
		'display': 'block',
		'height': n_layerHeight+'px'
	});
	$('#sendSms').removeClass('btnDisabled').unbind('click').bind('click', fn_sendBtn);	// 发送短信按钮事件
	$('.j_smsMsg').html('');
}


/*微信找开此页面显示提示*/
function fn_weixinDownload() {
	var n_clientHeight = document.documentElement.clientHeight,
		n_scrollHeight = document.documentElement.scrollHeight,
		n_clientWidth = document.documentElement.clientWidth,
		n_scrollWidth = document.documentElement.scrollWidth,
		n_layerHeight = n_clientHeight > n_scrollHeight ? n_clientHeight : n_scrollHeight,
		n_layerWidth = n_clientWidth > n_scrollWidth ? n_clientWidth : n_scrollWidth;
	
	$('#downloadLayer').addClass('iLayer').css({	// 添加遮罩层
		'display': 'block',
		'height': n_layerHeight+'px'
	}).show();
	$('#weixin_downloadDemo').show();
	
	$('#weixin_downloadImgPanel').attr('width', n_layerWidth/2);
	$('#weixin_downloadDemo').css({'width': n_layerWidth/2, 'left': n_layerWidth/4});
	
	$('#weixin_downloadKnow').unbind('click').click(function(e) {
		$('#weixin_downloadDemo').hide();
		$('#downloadLayer').removeClass().css({'display': 'none','height': '0px'}).hide();
	});
}