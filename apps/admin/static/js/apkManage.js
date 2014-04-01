/**
* APK管理相关操作
*/
$(function () {
	
	// 设置标题头样式
	$('#search_table th').addClass('ui-state-default');
	// 查询号码是否在白名单中事件侦听 
	$('#apk_search').click(function(e) {
		fn_validCookie();
		fn_initSearchApk();
		
	});
	// 新增初始化dialog
	$('#addApkDialog').dialog({
		autoOpen: false,
		height: 400,
		width: 590,
		position: [300, 100],
		modal: true,
		resizable: false
	});
	// 将APK新增事件侦听 
	$('#apk_upload').click(function(e) { 
		if ( fn_validCookie() ) {
			return;
		}
		var obj_currrentDate = new Date(),
			myDate = obj_currrentDate /1000,
			str_today = toTodayDate();
		
		$('#txt_apkVersionName, #txt_apkVersionCode, #txt_apkFileSize, #txt_apkInfo').val('');
		$('#filenamePanel').hide().val('');
		$('#fileBrowser').show();
		$('#fileUpload').val('');
		$('#sms_type_panel input[id="apkType_ydws"]').attr('checked', 'checked');
		
		$('#txt_apkUpdateTime').datepicker();
		$('#txt_apkUpdateTime').datepicker( 'option', 'dateFormat', 'yy-mm-dd' );
		$('#txt_apkUpdateTime').val(str_today);
		
		//APK上传的事件
		var obj_fileUpload = $('#fileUpload');
		
		obj_fileUpload.live('change', function(e) {
			var obj_filename = $('#filenamePanel'),
				n_filenameWidth = 0, 
				str_oldFilename = obj_filename.val(),
				str_filename = obj_fileUpload.val();
			
			if ( str_filename != '' ) {
				obj_filename.val(str_filename).show();
				n_filenameWidth = obj_filename.width();
				$('#fileUpload, .filePanel').css('width', n_filenameWidth);
				$('#fileBrowser').hide();
				
			} else {
				obj_fileUpload.val(str_oldFilename);
			}
		});
	
		$('#addApkDialog').attr('title', '新增APK').dialog('option', 'title', '新增APK').dialog('open');
		
	});
	
	$('#addApkSave').unbind('click').click(function(e) {
		var str_versionName = $('#txt_apkVersionName').val(),
			str_versionCode = $('#txt_apkVersionCode').val(),
			str_fileSize = $('#txt_apkFileSize').val(),
			str_updateTime= $('#txt_apkUpdateTime').val(),
			str_versionInfo = $('#txt_apkInfo').val(),
			str_apkType = $('input[name="apk_type"]:checked').val();
		
		if ( fn_validFileuploadForm() ) {
			$.ajaxFileUpload({
				url : '/apk',//用于文件上传的服务器端请求地址
				secureuri : false,//一般设置为false
				fileOperate: 'apkManage',
				fileElementId : 'fileUpload',//文件上传空间的id属性  <input type="file" id="files1" name="files1" /><input type="file" id="files2" name="files2" />
				fileParam: {
					versioncode: str_versionCode,// 版本号
					versionname: str_versionName,// 版本名
					versioninfo: str_versionInfo,// 版本信息
					updatetime: str_updateTime,// 更新时间
					filesize: str_fileSize,// 文件大小 
					author: decodeURIComponent($.cookie("ACBADMIN_N")),
					category: str_apkType //apk类型
				},
				dataType : 'json',//返回值类型 一般设置为json
				success : function(data, status) { //服务器成功响应处理函数
					if ( data.status == 0 ) {
						$('#addApkDialog').dialog('close');
						fn_initSearchApk();
					} else {
						$('#addApkDialog').dialog('close');
						$('#apk_upload').click();
					}
					alert(data.message);
					
				},
				error : function(data, status, e) {
					alert('服务器错误，请重新操作!');
				}
			});
		}
	});
	
	fn_initDataTables('apk', []);// 初始化表格显示
	fn_unLockScreen();
});

// 验证cookie是否超时
function fn_validCookie() {
	if(!$.cookie('ACBADMIN')) {
		alert('本次登录已经超时，系统将重新进入登录页面。');
		parent.window.location.replace('/login'); // redirect to the index.
		return true;
	}
	return false;
}


// 查询APK
function fn_initSearchApk() {
	var obj_tBody = $('#apk_tbody');
	
	obj_tBody.html('');
			
	$.post('/apk/list',  JSON.stringify(''), function (data) { 
		if ( data.status == 0 ) {
			var arr_tableData = [],
				arr_apkDatas = data.res,
				n_apkDataLen = arr_apkDatas.length;
			
			if ( n_apkDataLen <= 0 )  {
				str_tbodyText ='<tr><td colspan="6" class="sorting_1">无记录</td></tr>';
			} else {	
				for( var i = 0; i < n_apkDataLen; i++ ) {	
					var obj_tempApkData = arr_apkDatas[i],
						str_apkType = obj_tempApkData.category,
						str_apkTypeText = '移动卫士';
					
					if ( str_apkType == 1 ) {
						str_apkTypeText = '移动卫士'
					} else if ( str_apkType == 2 ) {
						str_apkTypeText = '移动外勤监控端'
					} else if ( str_apkType == 3 ) {
						str_apkTypeText = '移动外勤被监控端'
					} else if ( str_apkType == 4 ) {
						str_apkTypeText = '移动卫士--安捷通'
					}
					
					arr_tableData[i] = [obj_tempApkData.author, obj_tempApkData.versionname, obj_tempApkData.versioncode, str_apkTypeText, obj_tempApkData.versioninfo, obj_tempApkData.filesize, obj_tempApkData.updatetime, '<a href="#" onclick="fn_deleteApk('+obj_tempApkData.id+')">删除APK</a>'];
				}
			}			
			fn_initDataTables('apk', arr_tableData);
		} else {
			alert(data.message);
		}
	});
}

//================删除APK
function fn_deleteApk(str_id) {
	if ( str_id != '' ) {
		if ( confirm('您确定删除该APK吗？') ) {
			fn_lockScreen();
			$.delete_('/apk?ids='+str_id, '', function (data) { 
				fn_unLockScreen();
				fn_initSearchApk();
			});
		}
	}
}

//文件上传的验证
function fn_validFileuploadForm() {
	var str_file = $('#fileUpload').val(),
		str_versionName = $('#txt_apkVersionName').val(),
		n_versionCode = $('#txt_apkVersionCode').val(),
		str_fileSize = $('#txt_apkFileSize').val(),
		str_versionInfo = $('#txt_apkInfo').val();
	
	if ( str_file == '' ) {
		alert('请选择要上传的文件。');
		return false;
	} else if ( str_versionName == '' ) {
		alert('请填写APK名称。');
		return false;
	} else if ( n_versionCode == '' ) {
		alert('请填写APK版本。');
		return false;
	} else if ( !(/^\d*$/.test(n_versionCode)) ) {
		alert('APK版本填写错误。');
		return false;
	} else if ( str_fileSize == '' ) {
		alert('请填写APK大小。');
		return false;
	} else if ( !(/^\d+(\.\d{1,2}){0,1}$/.test(str_fileSize)) ) {
		alert('APK大小填写错误。');
		return false;
	} else if ( str_versionInfo == '' ) {
		alert('请填写APK描述。');
		return false;
	}
	return true;
}

/**
* jquery 异步请求架构
* url: ajax请求的url
* data: ajax请求参数
* callback: 回调函数
* errorCallback: 出现错误的回调函数
* method： ajax请求方式get or post
*/
function _ajax_request(url, data, callback, errorCallback, method) {
	return jQuery.ajax({
		type : method,
		url : url,
		data : data,
		success : callback,
        error : errorCallback, // 出现错误
		dataType : 'json',
		contentType : 'application/json; charset=utf-8',
        complete: function (XMLHttpRequest, textStatus) { // 页面超时
            var stu = XMLHttpRequest.status;
            if ( stu == 200 && XMLHttpRequest.responseText.search('captchaimg') != -1 ) {
                //window.location.replace('/static/timeout.html'); // redirect to the index.
                return;
            }
        }
	});
}

/**
* 继承并重写jquery的异步方法
*/
jQuery.extend({
    delete_: function(url, data, callback, errorCallback) {
        return _ajax_request(url, data, callback, errorCallback, 'DELETE');
    },
});
//==========================================================

function fn_initDataTables(str_who, obj_tableData) {
	var arr_ableTitle = ''; // 查询结果的结果头
	
	if ( str_who == 'apk' ) {
		arr_ableTitle = [
			{ 'sTitle': '上传人' },
			{ 'sTitle': 'APK版本名称' },
			{ 'sTitle': 'APK版本号' },
			{ 'sTitle': 'APK类型' },
			{ 'sTitle': 'APK描述' },
			{ 'sTitle': 'APK大小(M)' },
			{ 'sTitle': 'APK更新时间' },
			{ 'sTitle': '删除' }
		];
	}
	
	obj_searchDataTables = $('#'+str_who+'Search_table').dataTable({
		'bScrollCollapse': true,
		'aaSorting': [], // 默认不排序
		'bJQueryUI': true,
		'bProcessing': true,
		'bAutoWidth': false,
		'bDestroy': true, 
		'sPaginationType': 'full_numbers',  
		'aLengthMenu': [10, 20, 50, 100], //每页显示可调
		'iDisplayLength': 10, //默认每页20条记录
		'oLanguage': {
			'sUrl': '/static/js/dataTables.zh_CN.txt'
		},
		'aaData': obj_tableData, // 显示的数据
        'aoColumns': arr_ableTitle, // 结果头'
        'fnCreatedRow': function(nRow, aData, iDataIndex) {
			$(nRow).hover(function(){
				$(this).children().css({
					'background-color' : '#87CEFF'
				});
			},
			function(){
				$(this).children().removeAttr('style');
			});
        },
		'fnInitComplete': function(obj) {
			$('#'+str_who+'Search_table tr').hover(function(){
				$(this).children().css({
					'background-color' : '#87CEFF'
				});
				},
				function(){
					$(this).children().removeAttr('style');
				});
		}
	});
}