/**
* 登录、忘记密码功能
*/
var obj_updateTimeInterval =null;	// 找回密码倒数计时
$(function(){
	$.ajaxSetup({ cache: false }); // 不保存缓存
	var obj_captchaImg= $('#captchaimg'),	// 验证码图片存放对象
		n_bannerIndex = 0,	// 当前banner的编号
		currentAd = null;	// 图片轮换的计时器
	
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
	
	
	/**
	* 找回密码的相关事件绑定
	*/
	$('#btnGetPwd').click(function() {
		var str_val = $('#mobile').val(),
			str_msg = '',
			obj_param = {'mobile': str_val};
			
		
		if ( str_val == '' || str_val == null ) {	// 车主手机号不为空验证格式
			dlf.fn_jNotifyMessage('车主号码不能为空！', 'message', false, 3000);
			return;
		} else {
			var reg = MOBILEREG,
				n_seconds = parseInt($('#flashTimeText').html());
				
			if ( !reg.test(str_val) ) {	// 车主手机号合法性验证
				dlf.fn_jNotifyMessage('请填写正确的手机号！', 'message', false, 3000);
				return;
			}
			if ( n_seconds < 60 ) {	// 如果小于60 秒 不能发送
				$('#btnGetPwd').attr('disabled',true);
			} else {
				$('#btnGetPwd').removeAttr('disabled');
			}
			$.post_(PWD_URL, JSON.stringify(obj_param) , function(data) {
				if ( data.status == 0 ) { 
					fn_resetUpdateTime();	// 重新读秒操作
					$('#btnGetPwd').attr('disabled',true);
					str_msg = '您的密码已发送成功，请注意查收';
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
});

/**
* 每5秒 循环显示广告
*/
function fn_timer() {
	var n_nums = parseInt($('#adNums li[class=selected]').html()),
		obj_adNum = null,
		obj_content = null;
		
	if ( n_nums >= 6 ) {
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
