/*
* 终端列表功能 
*/
$(function() {
	// 初始化效果
	var n_imgPos = ($(window).width()-260)/2-20;
	
	if ( n_imgPos > 0 ) {
		$('.j_tlistImg').css('left', n_imgPos);
		$('.j_tlistUlPanel').css('left', n_imgPos+10);
	}
});

/* 设防/撤防功能  */
function fn_settingDefend(obj_imgItem, str_tid, str_defendSt) {
	var obj_defendData = {'tid': str_tid, 'mannual_status': ''},
		str_defnedText = '',
		str_dialogMsg = '';
	
	if ( str_defendSt == '1' ) {
		obj_defendData.mannual_status = '0';
		str_defnedText = '0';
		str_dialogMsg = '撤防进行中';
	} else {
		obj_defendData.mannual_status = '1';
		str_defnedText = '1';
		str_dialogMsg = '设防进行中';
	}
	
	fn_dialogMsg(str_dialogMsg+'<img src="/static/images/blue-wait.gif" />');
	$.post_('/defend', JSON.stringify(obj_defendData), function(data) {
		if ( data.status == 0 ) {
			$(obj_imgItem).attr('src', '/static/images/defend_status'+ obj_defendData.mannual_status +'.png?r=0.12138');
			$(obj_imgItem).attr('onClick', "fn_settingDefend(this, '"+ str_tid +"', '"+str_defnedText+"')");
		} else {
			alert(data.message);
		}
		fn_closeDialogMsg();
	});
}
