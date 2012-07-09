$(function(){
	$.ajaxSetup({ cache: false }); // 不保存缓存
    $('tr.input input').focus(function() {
        $(this).parent().parent().addClass('highlight');
    });
    $('tr.input input').blur(function(){
        $(this).parent().parent().removeClass('highlight');
    });
	// 调整登录按钮位置
	var obj_browser = $.browser, 
		obj_login = $('.commit')
		n_topNum = -15;
	if ( obj_browser.webkit ) {
		n_topNum = -25;
	} else if ( obj_browser.msie ) {
		var str_version = obj_browser.version;
		if ( str_version == '9.0' ) {
			n_topNum = -17;
		} else if ( str_version == '6.0' ) {
			n_topNum = -2;
		} else {
			n_topNum = 0;
		}
	}
	obj_login.css('top', n_topNum);
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
