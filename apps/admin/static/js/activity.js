/**
* 活动管理相关操作
*/
$(function () {
	
	// 设置标题头样式
	$('#search_table th').addClass('ui-state-default');
	// 查询号码是否在白名单中事件侦听 
	$('#activity_search').click(function(e) {
		fn_validCookie();
		fn_initSearchActivity();
		
	});
	// 新增初始化dialog
	$('#addActivityDialog').dialog({
		autoOpen: false,
		height: 300,
		width: 400,
		position: [300, 100],
		modal: true,
		resizable: false
	});
	// 将活动新增事件侦听 
	$('#activity_upload').click(function(e) { 
		if ( fn_validCookie() ) {
			return;
		}
		var obj_currrentDate = new Date(),
			myDate = obj_currrentDate /1000,
			str_today = toTodayDate();
		
		$('#txt_acticityTitle').val('');
		$('#filenamePanel').hide().val('');
		$('#fileBrowser').show();
		$('#fileUpload').val('');
		$('#txt_acticityStTime, #txt_acticityEndTime').datepicker();
		$('#txt_acticityStTime, #txt_acticityEndTime').datepicker( 'option', 'dateFormat', 'yy-mm-dd' );
		$('#txt_acticityStTime, #txt_acticityEndTime').val(str_today);
		//活动上传的事件
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
	
		$('#addActivityDialog').attr('title', '新增活动').dialog('option', 'title', '新增活动').dialog('open');
		
	});
	
	$('#addActivitySave').unbind('click').click(function(e) {
		var str_title = $('#txt_acticityTitle').val(),
			n_stTime = toEpochDate($('#txt_acticityStTime').val()+' 00:00:00'),
			n_endTime = toEpochDate($('#txt_acticityEndTime').val()+' 23:59:59');
		if ( n_stTime > n_endTime ) {
			alert('开始时间不能大于结束时间，请重新选择时间段。');
			return;
		}
	
		if ( fn_validFileuploadForm() ) {
			$.ajaxFileUpload({
				url : '/activity',//用于文件上传的服务器端请求地址
				secureuri : false,//一般设置为false
				fileElementId : 'fileUpload',//文件上传空间的id属性  <input type="file" id="files1" name="files1" /><input type="file" id="files2" name="files2" />
				activitytitle: str_title,
				sttime: n_stTime,
				endtime: n_endTime,
				author: decodeURIComponent($.cookie("ACBADMIN_N")),
				dataType : 'json',//返回值类型 一般设置为json
				success : function(data, status) { //服务器成功响应处理函数
					if ( data.status == 0 ) {
						$('#addActivityDialog').dialog('close');
						fn_initSearchActivity();
					} else {
						$('#addActivityDialog').dialog('close');
						$('#activity_upload').click();
					}
					alert(data.message);
					
				},
				error : function(data, status, e) {console.log('xxx:  ',data, status, e);
					alert('服务器错误，请重新操作!');
				}
			});
		}
	});
	
	fn_initDataTables('activity', []);// 初始化表格显示
	fn_unLockScreen();
});

// 验证cookie是否超时
function fn_validCookie() {
	if(!$.cookie('ACBADMIN')) {
		alert('本次登陆已经超时，系统将重新进入登陆页面。');
		parent.window.location.replace('/login'); // redirect to the index.
		return true;
	}
	return false;
}


// 查询活动
function fn_initSearchActivity() {
	var str_stTime = $('#start_time1').val(),
		str_endTime = $('#end_time1').val(),
		obj_tBody = $('#activity_tbody');
	
	obj_tBody.html('');
			
	$.post('/activity/list',  JSON.stringify(''), function (data) { 
		if ( data.status == 0 ) {
			var arr_tableData = [],
				arr_activityDatas = data.res,
				n_activityDataLen = arr_activityDatas.length;
			
			if ( n_activityDataLen <= 0 )  {
				str_tbodyText ='<tr><td colspan="6" class="sorting_1">无记录</td></tr>';
			} else {	
				for( var i = 0; i < n_activityDataLen; i++ ) {	
					var obj_tempActivityData = arr_activityDatas[i];
								
					arr_tableData[i] = [obj_tempActivityData.title, obj_tempActivityData.filename, obj_tempActivityData.author, toHumanDate(obj_tempActivityData.begintime), toHumanDate(obj_tempActivityData.endtime),'<a href="#" onclick="fn_deleteActivity('+obj_tempActivityData.id+')">删除活动</a>'];
				}
			}			
			fn_initDataTables('activity', arr_tableData);
		} else {
			alert(data.message);
		}
	});
}

//================删除活动
function fn_deleteActivity(str_id) {
	if ( str_id != '' ) {
		if ( confirm('您确定删除活动吗？') ) {
			fn_lockScreen();
			$.delete_('/activity?ids='+str_id, '', function (data) { 
				fn_unLockScreen();
				fn_initSearchActivity();
			});
		}
	}
}
//文件上传的验证
function fn_validFileuploadForm() {
	var str_file = $('#fileUpload').val(),
		txt_acticityTitle = $('#txt_acticityTitle').val();
	
	if ( str_file == '' ) {
		alert('请选择要上传的文件。');
		return false;
	} else if ( txt_acticityTitle == '' ) {
		alert('请填写活动名称。');
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
	
	if ( str_who == 'activity' ) {
		arr_ableTitle = [
			{ 'sTitle': '活动名称' },
			{ 'sTitle': '活动图片' },
			{ 'sTitle': '活动上传人' },
			{ 'sTitle': '活动开始时间' },
			{ 'sTitle': '活动结束时间' },
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