/**
* 登录、忘记密码功能
*/
var obj_updateTimeInterval =null;	// 找回密码倒数计时
$(function(){
	$.ajaxSetup({ cache: false }); // 不保存缓存
	
	if ( DOMAIN_HOST == 'ajt.zhydgps.com' || DOMAIN_HOST == 'ajt.ichebao.net' ) { 
		document.title='安捷通--登录';
		$('.top').css('background-image', 'url("/static/images/loginBg_ajt.png")');
		$('#font_tipContent').html('安捷通');
	} 
	
	var obj_captchaImg= $('#captchaimg'),	// 验证码图片存放对象
		n_bannerIndex = 0,	// 当前banner的编号
		currentAd = null,	// 图片轮换的计时器
		str_type = $.cookie('USERCURRENTROLE'),
		obj_tabs = $('.tabs li'),
		obj_first = obj_tabs.eq(0),
		obj_sed = obj_tabs.eq(1),
		obj_individualPanel = $('.j_personal'),
		obj_corp = $('.j_corp'),
		obj_userGetPwd = $('#getPwd'),
		obj_corpGetPwd = $('#corpGetPwd');
	
	if ( str_type == 'enterprise' ) {	// 集团用户
		$('#userRoleType').val('enterprise');
		obj_sed.removeClass('other').addClass('current');
		obj_first.removeClass('current').addClass('other');
		/*obj_userGetPwd.hide();
		obj_corpGetPwd.show();*/
		obj_individualPanel.hide();
		obj_corp.show();
	} else {
		$('#userRoleType').val('individual');
		obj_sed.removeClass('current').addClass('other');
		obj_first.removeClass('other').addClass('current');
		/*obj_userGetPwd.show();
		obj_corpGetPwd.hide();*/		
		obj_individualPanel.show();
		obj_corp.hide();
	}
	
	/**
	* tab 选项卡
	*/
	$('.tabs li').unbind('click').bind('click', function() {
		var obj_this = $(this),
			str_userType = obj_this.attr('userType'),
			b_current = obj_this.hasClass('current'),
			obj_userType = $('#userRoleType'),
			obj_individualPanel = $('.j_personal'),
			obj_corp = $('.j_corp'),
			obj_userGetPwd = $('#getPwd'),
			obj_corpGetPwd = $('#corpGetPwd');
		
		obj_userType.val(str_userType);
		$('#username').val('');
		$('#password').val('');
		$('#captcha').val('');
		$('.txtColor').html('');
		if ( !b_current ) {
			obj_this.siblings().removeClass('current').addClass('other');
			obj_this.removeClass('other').addClass('current');
		}
		if ( str_userType == 'individual' ) {
			obj_corp.hide();
			obj_individualPanel.show();
			/*obj_userGetPwd.show();
			obj_corpGetPwd.hide();*/
		} else {
			obj_individualPanel.hide();
			obj_corp.show();
			/*
			obj_userGetPwd.hide();
			obj_corpGetPwd.show();
			*/
		}
		$.cookie('USERCURRENTROLE', str_userType, {expires:365});
	});
	
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
	fn_getCaptcha(obj_captchaImg);
	
	$('#adNums li').eq(0).removeClass('default').addClass('selected').siblings().removeClass('selected').addClass('default');	// 设置第一张图片为选中样式，其余为默认样式
	
	/**
	* 鼠标移上去显示相应广告 并停止计时
	*/
	$('#adNums li').mouseover(function() {
		var n_index = $(this).index(); //当前li的index
		
		$(this).siblings().removeClass('selected').addClass('default'); //兄弟节点默认样式
		$(this).removeClass('default').addClass('selected');	// 当前节点 选中样式
		$('#contents li').siblings().hide();
		$('#contents li').eq(n_index).show();
		clearInterval(currentAd);
	}).mouseout(function() {	// 鼠标移开 计时开始
		n_bannerIndex = $(this).index();
		currentAd = setInterval(fn_timer, 5000);
	});
	
	currentAd = setInterval(fn_timer, 5000);
	
	$('#jNotifyMessage').css('top', 50);
	$('#mobile').val('').keyup(function(e) {
		$('#btnGetCaptcha').removeAttr('disabled');
	});
	$('#pwd_captcha').val('');
	// 找回密码获取验证码
	$('#btnGetCaptcha').click(function() {
		var str_val = $('#mobile').val(),
			obj_param = {'mobile': str_val},
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
				} else {
					str_msg = data.message;
				}
				dlf.fn_jNotifyMessage(str_msg, 'message', false, 3000);
			}, 
			function(XMLHttpRequest, textStatus, errorThrown) {
				dlf.fn_serverError(XMLHttpRequest);
			});
		}
	}).attr('disabled',true);
	
	/**
	* 找回密码的相关事件绑定
	*/
	$('#btnGetPwd').click(function() {
		var str_val = $('#mobile').val(),
			str_captchaVal = $('#pwd_captcha').val(),
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
				$('#btnGetPwd').attr('disabled',true);
			} else {
				$('#btnGetPwd').removeAttr('disabled');
			}
			$.post_(str_url, JSON.stringify(obj_param) , function(data) {
				if ( data.status == 0 ) { 
					fn_resetUpdateTime();	// 重新读秒操作
					$('#btnGetPwd').attr('disabled',true);
					str_msg = '您的密码已发送成功，请注意查收。';
				} else {
					str_msg = data.message;
				}
				dlf.fn_jNotifyMessage(str_msg, 'message', false, 3000);
			}, 
			function(XMLHttpRequest, textStatus, errorThrown) {
				dlf.fn_serverError(XMLHttpRequest);
			});
		}
	});
	
	// 体验
	$('#login_ty').click(function(e) {
		$('#login_tyForm').submit();
	});	
});

/**
* 每5秒 循环显示广告
*/
function fn_timer() {
	var n_nums = parseInt($('#adNums li[class=selected]').html()),
		obj_adNum = null,
		obj_content = null;
		
	if ( n_nums >= 4 ) {
		n_nums = 0;
	}	
	obj_adNum = $('#adNums li').eq(n_nums);
	obj_content = $('#contents li').eq(n_nums);	
	
	obj_adNum.removeClass('default').addClass('selected');
	obj_adNum.siblings().removeClass('selected').addClass('default');
	
	obj_content.show();
	obj_content.siblings().hide();
	n_nums++;
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
			$('#btnGetPwd').removeAttr('disabled');
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

/**
* 验证码图片及hash值得设置
*/
function fn_getCaptcha($obj) {
	$obj.attr('src', '/captcha?nocache=' + Math.random()).load(function () {
		$('#captchahash').val($.cookie('captchahash'));
	});
}


/**
* 对登录字段处理
*/
function fn_validLogin() {
	var str_loginName = $('#login_username').val(),
		str_loginPwd = $('#login_pwd').val(),
		str_loginCaptcha = $('#login_captcha').val(),
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
