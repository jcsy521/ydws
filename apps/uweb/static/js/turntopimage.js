/**
*头部广告轮换
*/
$(function() {
	var n_index = 1,
		currentAd = null;
	/*主页面 广告幻灯片效果*/
	function fn_timer() {
		var obj_ad =  $('#contents img'),
			n_index = parseInt(obj_ad.attr('index'));
		obj_ad.fadeOut(function() {
			if ( n_index < 3 ) {
				n_index++;
			} else {
				n_index = 1;
			}
			obj_ad.attr('index', n_index);
			$(this).attr('src', '/static/images/banner'+ n_index +'.jpg').fadeIn(1000);
		});
	}
	// 计时器 
	currentAd = setInterval(function () { // 每5秒
		fn_timer();
	}, 4000);
});