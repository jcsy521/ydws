$(function() {
	var n_gid = parent.document.getElementById('hidGid').value,
		str_gname = parent.document.getElementById('hidGName').value;
	
	$('#gid').val(n_gid);
	$('.j_thead').html('组名：'+str_gname);
	$('.j_active').attr('disabled', false);
	// 选择文本框和浏览按钮实现file的click事件
	$('#btnFileUpload, #txtFile').click(function() {	
		$('#upload_file').click();
	});
	// file 的change事件
	$('#upload_file').unbind('change').bind("change", function() {	
		var obj_this = $(this),
			obj_msg = $('.j_uploadError'),
			str_val = obj_this.val();
		
		obj_msg.html('');
		$('#txtFile').val(str_val);
		var str  = str_val.substr(str_val.lastIndexOf('.') + 1, str_val.length);
		// 上传文件后判断后缀名
		if ( str != 'xlsx' && str != 'xls' ) {
			obj_msg.html('上传文件格式错误，请重新上传。');
			obj_this.val('');
			$('.j_startUpload').hide();
		} else {
			$('.j_startUpload').show();
		}
	});				
	// 批量激活事件
	$('.j_active').unbind('click').bind('click', function() {
		var obj_notActive = $('.j_notActived'),
			obj_resultTab = $('#fileUploadTable'),
			arr_mobiles = [],
			obj_param = {'gid': n_gid, 'mobiles': []};
		
		$.each(obj_notActive, function() {
			var obj_this = $(this),
				str_tmobile = obj_this.attr('tmobile'),
				str_umobile = obj_this.attr('umobile'),
				str_biztype = obj_this.attr('bizType');
				
			arr_mobiles.push({'tmobile': str_tmobile, 'umobile': str_umobile, 'biz_type': str_biztype});
		});
		
		if ( arr_mobiles.length > 0 ) {
			dlf.fn_jNotifyMessage('定位器正在激活中...<img src="/static/images/blue-wait.gif" width="12px" />', 'message', true);
			obj_param.mobiles = arr_mobiles;
			$.post_('/batch/JH', JSON.stringify(obj_param),function(data) {
				if ( data.status == 0 ) {
					var arr_datas = data.res;
					
					dlf.fn_closeJNotifyMsg('#jNotifyMessage');
					for ( var x = 0; x < arr_datas.length; x++ ) {
						var obj_result = arr_datas[x],
							n_status = obj_result.status,
							str_tmobile = obj_result.tmobile,
							obj_updateTd = $('.j_notActived[tmobile='+ str_tmobile +']').children('td').eq(3);
						
						if ( n_status == 0 ) {
							obj_updateTd.html('激活指令已下发').addClass('fileStatus4');
						} else {
							obj_updateTd.html('激活失败').addClass('fileStatus3');
						}
					}
					$('.j_active').removeClass('beginUploadBtn').addClass('btn_delete').attr('disabled', true);
					
					parent.dlf.fn_corpGetCarData();
					dlf.fn_closeJNotifyMsg('#jNotifyMessage');  // 关闭消息提示
				} else {
					dlf.fn_jNotifyMessage('定位器激活失败，请重新激活。', 'message', false, 3000);
					return;
				}
			}, 
			function (XMLHttpRequest, textStatus, errorThrown) {
				dlf.fn_serverError(XMLHttpRequest);
			});
		} else {
			dlf.fn_jNotifyMessage('定位器号码不合法，请确认后重试。', 'message', false, 3000);
			return;
		}
	});
});