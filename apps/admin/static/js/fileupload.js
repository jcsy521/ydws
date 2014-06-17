$(function() {
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
			obj_param = {'mobiles': []};
		
		$.each(obj_notActive, function() {
			var obj_this = $(this),
				str_tmobile = obj_this.attr('tmobile');
				
			arr_mobiles.push(str_tmobile);
		});
		
		if ( arr_mobiles.length > 0 ) {
			obj_param.mobiles = arr_mobiles;
			$.post('/whitelist/batch/add', JSON.stringify(obj_param), function(data) {
				if ( data.status == 0 ) {
					var arr_datas = data.res;
					
					for ( var x = 0; x < arr_datas.length; x++ ) {
						var obj_result = arr_datas[x],
							n_status = obj_result.status,
							str_tmobile = obj_result.mobile,
							obj_updateTd = $('.j_notActived[tmobile='+ str_tmobile +']').children('td').eq(1);
						
						if ( n_status == 0 ) {
							obj_updateTd.html('添加成功').addClass('fileStatus4');
						} else {
							obj_updateTd.html('添加失败').addClass('fileStatus3');
						}
					}
					$('.j_active').remove();
				} else {
					alert('白名单添加失败，请重新添加。');
				}
			});
		} else {
			alert('白名单号码不合法，请确认后重试。');
		}
	});
});
