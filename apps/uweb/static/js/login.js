$(function(){
	$.ajaxSetup({ cache: false }); // 不保存缓存
    $('tr.input input').focus(function() {
        $(this).parent().parent().addClass('highlight');
    });
    $('tr.input input').blur(function(){
        $(this).parent().parent().removeClass('highlight');
    });
	var index = 0,
		currentAd = null;
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
		}, 1000);
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
