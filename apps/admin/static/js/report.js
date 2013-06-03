/**
* kjj 2013-05-31 create
* 报表统计功能
*/

$(function() {
	// 编辑备注click事件
	$('.j_remark').unbind('click blur focus').blur(function() {	// 失去焦点
		var obj_this = $(this);

		obj_this.removeClass('remarkFocusCss').addClass('remarkBlurCss');
		obj_this.removeAttr('disabled');
		
		fn_editOfflineRemark(obj_this);
		// obj_this.parent().unbind('click');
	}).focus(function() {	// 获得焦点
		var obj_this = $(this);
		
		obj_this.val(obj_this.attr('val'));
		// 显示label 隐藏文本框
		obj_this.removeClass('remarkBlurCss').addClass('remarkFocusCss');
		obj_this.attr("disabled",false); 
	}).css('width', '300px');
});

/**
* 离线用户统计 添加备注功能
*/
function fn_editOfflineRemark(obj_this) {
	var n_index = $(this).parent().index(),
		str_id = obj_this.attr('remarkId'),
		str_oldVal = obj_this.attr('val'),
		str_val = obj_this.val(),
		str_tempVal = '',
		obj_data = {};
	
	str_tempVal = str_val.length > 20 ? str_val.substr(0,20) + '...' : str_val;
	// 如果旧val  和新val不相同发送put请求 
	if ( str_id && ( str_oldVal != str_val ) ) {	
		obj_data.id = parseInt(str_id);
		obj_data.remark = str_val;
	
		jQuery.ajax({
			type : 'put',
			url : '/report/offline',
			data : JSON.stringify(obj_data),
			dataType : 'json',
			contentType : 'application/json; charset=utf-8',
			complete: function (XMLHttpRequest, textStatus) {
				var stu = XMLHttpRequest.status;				
				
				if ( stu == 200 ) {
					obj_this.val(str_tempVal).attr('title', str_val).attr('val', str_val).removeClass('remarkFocusCss').addClass('remarkBlurCss');
					return;
				} else {
					obj_this.removeClass('remarkBlurCss').addClass('remarkFocusCss').removeAttr('disabled');
					alert('保存失败，请重新再试。');
					return false;
				}
			}
		});
	} else {
		obj_this.val(str_tempVal).removeClass('remarkFocusCss').addClass('remarkBlurCss').removeAttr('disabled');
	}
}

