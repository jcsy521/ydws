﻿var updateTimeInterval = null,
 	obj_updateTimeInterval =null;
$(function(){
	$.ajaxSetup({ cache: false }); // 不保存缓存
	// input css
	$('tr.input input').focus(function() {
		$(this).parent().parent().addClass('highlight');
	});
	$('tr.input input').blur(function(){
		$(this).parent().parent().removeClass('highlight');
	});

	var index = 0,
		currentAd = null;
	// set all ad default , set the first ad seleted
	$('#adNums li').removeClass('seleted').addClass('default');
	$('#adNums li').eq(0).removeClass('default').addClass('seleted');
	// 鼠标移上去显示相应广告 并停止计时
	$('#adNums li').mouseover(function() {
		var n_index = $(this).index(); //当前li的index
		$(this).siblings().removeClass('seleted').addClass('default'); //兄弟节点默认样式
		$(this).removeClass('default').addClass('seleted');	// 当前节点 选中样式
		$('#contents li').siblings().hide();
		$('#contents li').eq(n_index).show();
		clearInterval(currentAd);
	}).mouseout(function() {	// 鼠标移开 计时开始
		index = $(this).index();
		currentAd = setInterval(function () { // 每5秒
			fn_timer();
		}, 5000);
	});

	// 每5秒 循环显示广告
	function fn_timer() {
		var obj_nums = $('#adNums li').eq(index),
			obj_content = $('#contents li').eq(index);
		obj_nums.siblings().removeClass('seleted').addClass('default'); //兄弟节点默认样式
		obj_nums.removeClass('default').addClass('seleted');	// 当前节点 选中样式
		obj_content.siblings().hide();
		obj_content.show();
		if ( index <5 ) {
			index++;
		} else {
			index = 0;
		}
	}
	// 计时器 
	currentAd = setInterval(function () { // 每5秒
		fn_timer();
	}, 5000);
	
	/*---------找回密码功能------------*/
	
	// 更新数据获取时间
	function fn_updateTime() {
		obj_updateTimeInterval = setInterval(function() {
			var obj_updateTime = $('#flashTimeText'),
				str_updateTime = obj_updateTime.html();
			console.log('111111111');
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
	// 重新启动读秒操作
	function fn_resetUpdateTime() {
		dlf.fn_clearInterval(obj_updateTimeInterval);
		$('#flashTimeText').html(60);
		$('#seconds').show();
		fn_updateTime();
	}
	$('#btnGetPwd').click(function() {
		var param = {'mobile': $('#mobile').val()};
		// 如果小于60 秒 不能发送
		var n_seconds = parseInt($('#flashTimeText').html());
		if ( n_seconds < 60 ) {
			$('#btnGetPwd').attr('disabled',true);
		} else {
			$('#btnGetPwd').removeAttr('disabled');
		}
		$.post_(PWD_URL, JSON.stringify(param) , function(data) {
			if ( data.status == 0 ) {  // success
				fn_resetUpdateTime();
				$('#btnGetPwd').attr('disabled',true);
			}
			dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
		}, 
		function(XMLHttpRequest, textStatus, errorThrown) {
			dlf.fn_serverError(XMLHttpRequest);
		});
	});
});

window.onload = function() {
	var $imgElem = $('#captchaimg');
	$imgElem.click(function () {
		fn_getCaptcha($(this));
	});
	fn_getCaptcha($imgElem);
	// 获取后台验证码
	function fn_getCaptcha($obj) {
		$obj.attr('src', '/captcha?nocache=' + Math.random()).load(function () {
			$('#captchahash').val($.cookie('captchahash'));
		});
	}
}
