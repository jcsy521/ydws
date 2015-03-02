/*
 * 脚本上传
 */
$(function() {
	$('#search_table').dataTable({
		'bScrollCollapse': true,
		'aaSorting': [], // 默认不排序
		'bJQueryUI': true,
		'bProcessing': true,
		'bAutoWidth': false,
		'bDestroy': true,
		'sPaginationType': 'full_numbers',
		'aLengthMenu': [20, 50, 100], //每页显示可调
		'iDisplayLength': 20, //默认每页20条记录
		'oLanguage': {
			'sUrl': '/static/js/dataTables.zh_CN.txt'
		}
	});
	$('#search_table tr').hover(function() {
			$(this).children().css({
				'background-color': '#87CEFF'
			});
		},
		function() {
			$(this).children().removeAttr('style');
		});
	$('#search_table').css('width', '100%');

	/*================================*/
	// 添加脚本 单击事件
	var obj_fileuploadDialog = $('#fileUploadDialog');

	$('#addTerminalScript').unbind('click').bind('click', function() {
		$('#fileUpload, #versionname').val('');
		$('#filenamePanel').val('').hide();
		$('#fileBrowser').show();
		obj_fileuploadDialog.attr('title', '上传脚本').dialog('option', 'title', '上传脚本').dialog("open");
	});
	// 新增初始化dialog
	obj_fileuploadDialog.dialog({
		autoOpen: false,
		height: 200,
		width: 370,
		modal: true,
		resizable: false
	});

	//文件上传的事件
	var obj_fileUpload = $('#fileUpload');

	obj_fileUpload.change(function(e) {
		var obj_filename = $('#filenamePanel'),
			n_filenameWidth = 0,
			str_oldFilename = obj_filename.val(),
			str_filename = obj_fileUpload.val();

		if (str_filename != '') {
			obj_filename.val(str_filename).show();
			n_filenameWidth = obj_filename.width();
			$('#fileUpload, .filePanel').css('width', n_filenameWidth);
			$('#fileBrowser').hide();

		} else {
			obj_fileUpload.val(str_oldFilename);
		}
	});
});

//================删除脚本
function fn_terminalDel(str_fileName, n_islocked) {
		if (str_fileName != '') {
			if (n_islocked == 1) {
				alert('脚本被锁定，请先解锁。');
				return;
			}
			if (confirm('您确定删除脚本吗？')) {
				window.location.href = '/deleteluascript?filename=' + str_fileName;
			}
		}
	}
	//文件上传的验证
function fn_validFileuploadForm() {
	var str_file = $('#fileUpload').val(),
		str_version = $('#versionname').val();

	if (str_file == '') {
		alert('请选择要上传的文件。');
		return false;
	} else if (str_version == '') {
		alert('请填写版本号。');
		return false;
	}
	return true;
}

// 脚本锁定 解锁
function fn_lockscript(n_islocked, n_id) {
	var str_tips = '',
		str_returnMsg = '',
		str_targetHtml = '',
		obj_params = {
			'islocked': 0,
			'id': parseInt(n_id)
		};

	if (n_islocked == 1) {
		str_tips = '您确定解锁脚本吗？';
	} else {
		str_tips = '您确定锁定脚本吗？';
		obj_params.islocked = 1;
	}
	if (confirm(str_tips)) {
		$.put_('/uploadluascript', JSON.stringify(obj_params), function(data) {
			if (data.status == 0) {
				alert('操作成功。');
				location.reload();
			} else {
				alert('操作失败，请稍后再试。');
				return;
			}
		});
	}
}