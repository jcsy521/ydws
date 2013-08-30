/**
* 查询集合文件
* chart: 统计图对象
* obj_searchDataTables: datatables 对象
*/
var chart = null, 
	obj_searchDataTables = null;


/**
* 初始化查询条件
*/
function fn_initRecordSearch(str_who) {
	if (fn_validCookie()) {
		return;
	}
	fn_setTitleName();  // 调整标题用户名位置
	
	fn_initDataTables('search_table', str_who, []);// 初始化表格显示
	
	$('#search_button').unbind('click').bind('click', function() {	// 查询数据事件
		fn_searchData(str_who);
	});
	
	// 为报文查询的全选按钮和具体报文类型添加事件
	if ( str_who == 'packet' ) {
		var obj_allCheck = $('#packet_all_type'),
			obj_packetType = $('#packetTypes input[name=packet_type]');
		// 选中状态初始化
		$('#packetTypes input[name=packet_type], #packet_all_type, #packet_report_type').removeAttr('checked');
		
		//全选的事件
		obj_allCheck.click(function(e) {
			var str_allCheck = $(this).attr('checked');
			
			if ( str_allCheck ) { 
				obj_packetType.attr('checked', 'checked');
			} else {
				obj_packetType.removeAttr('checked');
			}
		});
		
		// 单个类型的事件
		obj_packetType.click(function(e) {
			var obj_this = $(this),
				str_html = obj_this.val(),
				str_check = obj_this.attr('checked');
				
			if ( !str_check ) { 
				obj_allCheck.removeAttr('checked');
			} else {
				if ( fn_validPacketTypeCheck() ) {
					obj_allCheck.attr('checked', 'checked');
				}
			}
			
		});
	
	}
}

/**
* 拼凑查询参数并查询数据
* str_who: 根据wrapper来拼凑查询参数
*/
function fn_searchData(str_who) {
	fn_validCookie();
	
	var obj_conditionData = {}, 
		str_getDataUrl = '';
	
	switch (str_who) {
		case 'log': //  日志查询
			
			var str_stTime = $('#beginDate').val(), 
				str_entTime = $('#endDate').val(), 
				str_planId = $('#plan_id').val(), 
				str_levelId = $('#level_id').val(); 
			
			if ( !fn_validSearchDate() ) {
				return;
			}
			obj_conditionData = {
				'start_time': str_stTime,
				'end_time': str_entTime,
				'plan_id': str_planId,
				'level': str_levelId
			};
			str_getDataUrl = '/systemlog';
			
			break;
		case 'packet': //  报文查询
			
			var str_stTime = $('#beginDate').val(), 
				str_entTime = $('#endDate').val(), 
				str_terminalNum = $('#terminal_num').val(), 
				n_snType = $('#snTypePanel input[name="sn_type"]input:checked').val(),
				str_message_type = '',
				b_packetReport = $('#packet_report_type').attr('checked'),
				n_packetReport = b_packetReport ? 1 : 0; // 是否要回调报文 
			
			if ( n_snType == 0 ) {
				if ( !fn_validMobile(str_terminalNum) ) {
					return;
				}
			} else {
				if ( !fn_validTerminalSn(str_terminalNum) ){
					return;
				}
			}
			
			if ( !fn_validSearchDate() ) {
				return;
			}
			
			$('#packetTypes input[name=packet_type]').each(function(e) {
				var str_checked = $(this).attr('checked'),
					str_check_type = $(this).val();
				
				if ( str_checked ) { 
					if ( str_check_type != 'T17' && str_check_type != 'T25' ) {
						str_message_type += '|'+ str_check_type +',';
					} else {
						str_message_type += '|'+ str_check_type;
					}
				}
			});
			
			// 是否选择了报文类型
			if ( str_message_type.length <= 0 ) {
				//str_message_type = 'T1,|T2,|T3,|T4,|T5,|T6,|T7,|T8,|T9,|T10,|T11,|T12,|T13,|T14,|T15,|T16,|T17|T18,|T19,|T20,|T21,|T22,|T23,|T24,|T25';
				alert('请选择您要查询的报文类型。');
				return;
			} else {
				str_message_type = str_message_type.substr(1, str_message_type.length);
			}
			
			obj_conditionData = {
				'start_time': fn_changeDateStringToFormat(str_stTime),
				'end_time': fn_changeDateStringToFormat(str_entTime),
				'mobile': str_terminalNum,
				'sn': str_terminalNum,
				'search_type': n_snType,
				'is_report': n_packetReport,
				'packet_types': '('+str_message_type+')'
			};
			str_getDataUrl = '/packet';
			
			break;
		case 'battery': //  电量查询
			
			var str_stTime = $('#beginDate').val(), 
				str_entTime = $('#endDate').val(), 
				n_snType = $('#snTypePanel input[name="sn_type"]input:checked').val(),
				str_terminalNum = $('#terminal_num').val();
				
			if ( n_snType == 0 ) {
				if ( !fn_validMobile(str_terminalNum) ) {
					return;
				}
			} else {
				if ( !fn_validTerminalSn(str_terminalNum) ){
					return;
				}
			}
				
			if ( !fn_validSearchDate() ) {
				return;
			}	
			obj_conditionData = {
				'start_time': fn_changeDateStringToFormat(str_stTime),
				'end_time': fn_changeDateStringToFormat(str_entTime),
				'mobile': str_terminalNum,
				'sn': str_terminalNum,
				'search_type': n_snType
			};
			str_getDataUrl = '/battery';
			
			$('#battery_chart_link').hide();
			break;
		case 'feedback':	// 意见反馈
			var str_stTime = $('#beginDate').val(), 
				str_entTime = $('#endDate').val(), 
				n_reply = $('input:checked').val();
				
			obj_conditionData = {
				'start_time': fn_changeDateStringToNum(str_stTime),
				'end_time': fn_changeDateStringToNum(str_entTime),
				'isreplied': parseInt(n_reply)
			};
			str_getDataUrl = '/feedback';
			
			break;
	}
	
	fn_lockScreen();
	$.post(str_getDataUrl,  JSON.stringify(obj_conditionData), function (data) { 
		fn_unLockScreen();
		fn_bindSearchRecord(str_who, data);
	});
}
/**
* 绑定页面连接及操作的事件 
*/
function fn_bindSearchRecord(str_who, obj_resdata) {
	var arr_recordData = null;
			
	if ( obj_resdata.status == 0 ) {  // success
		arr_recordData = obj_resdata.res; 
		/*	统一改成 res
		if ( str_who == 'log' ) { //日志查询
			arr_recordData = obj_resdata.log_list;
		} else if ( str_who == 'packet' ) { //报文查询
			arr_recordData = obj_resdata.packet_list;
		} else if ( str_who == 'battery' ) { //电量查询
			arr_recordData = obj_resdata.battery_list;
		} else if ( str_who == 'feedback' ) {	// 意见反馈
			arr_recordData = obj_resdata.feedback_list;
		}*/
		
		fn_productTableContent(str_who, arr_recordData);	// 根据页面的不同生成相应的table表格
	} else {
		alert(obj_resdata.message);	
	}
}

String.prototype.len=function() {              
	return this.replace(/[^\x00-\xff]/g,"rr").length;          
}

/**
* 根据数据和页面不同生成相应的table域内容
*/
function fn_productTableContent(str_who, obj_reaData) {
		
	var n_searchLen = obj_reaData.length, 
		obj_searchHeader = $('#search_tbody'), 
		arr_tableData = [],
		arr_categories = [], 
		arr_graphic_x = new Array(n_searchLen),// 统计表的时间字段x
		arr_graphic = [], //统计表的电量字段y
		obj_chart = null, 
		str_unit = '%', //单位
		str_container = 'batteryChart_panel', // 容器名称
		obj_chartDialog = $('#batteryChart_dialog');
	
	if (n_searchLen > 0) {
		for( var i = 0; i < n_searchLen; i++ ) {	
			var obj_tempData = obj_reaData[i];
			
			if ( obj_tempData ) {
				switch (str_who) {
					case 'log': // 日志查询
						arr_tableData[i] = [obj_tempData.time,obj_tempData.servername,obj_tempData.level,obj_tempData.details, '<a href="/detail?id='+obj_tempData.id+'" target="_blank" >查看详细</a>'];	
						break;
					case 'packet': // 报文查询
						arr_tableData[i] = [obj_tempData.packet_time,obj_tempData.packet_type,obj_tempData.packet];	
						break;
					case 'battery': // 电量查询
						var str_batteryTime = obj_tempData.battery_time, 
							str_battery = obj_tempData.battery_num;
						
						arr_tableData[i] = [str_batteryTime,str_battery];	
						arr_graphic.push(parseInt(str_battery)); // 每个时间点的电量信息
						arr_categories.push(str_batteryTime);
						arr_graphic_x[i] = '';
						break;
					case 'feedback':	// 意见反馈
						var str_contact = obj_tempData.contact,	// 联系人
							str_email = obj_tempData.email,	// 客户邮箱
							str_content = obj_tempData.content,	// 反馈内容
							str_publishTime = obj_tempData.timestamp,	// 反馈意见时间
							n_reply = obj_tempData.isreplied,	// 是否回复邮件
							str_replyTime = obj_tempData.reply_time,	// 回复时间
							str_tempReplyTime = str_replyTime == 0 ? '' : fn_changeNumToDateString(str_replyTime),
							str_replyContent = obj_tempData.reply,	// 回复内容
							str_hide = n_reply == 0 ? 'hide' : '',
							str_show = n_reply == 1 ? 'hide' : '',
							n_feedbackId = obj_tempData.id,	// 记录ID 用来删除和编辑
							str_html = '';
							
						str_contact = str_contact == '' ? str_email : str_contact;
						str_html = '<div class="item" id="item'+ n_feedbackId +'"><div class="user"><span class="u_name">客户名称：'+ str_contact +'</span><span class="u_email">email：'+ str_email +'</span><span class="date-ask">'+ fn_changeNumToDateString(str_publishTime) +'</span><span class="operation">';
						
						str_html += '<a href="#" onclick="fn_editReply(this, '+ n_feedbackId +')">编辑回复</a>';
						// 有回复
						if ( n_reply == 1 ) {
							str_html += '<font class="green">已回复</font>';
						} else {
							str_html += '<font class="red">未回复</font>';
						}
						str_html += '<a href="#" onclick="fn_deleteFeedback('+ n_feedbackId +')">删除反馈</a></span></div>';
						str_html += '<dl class="ask"><dt>反馈内容：</dt><dd><label>'+ str_content +'</label></dd></dl>';
						str_html += '<dl class="answer j_answer"><dt class="'+ str_hide +'">客服回复：</dt>';
						
						str_html += '<dd class="'+ str_hide +' j_replyContent"><div class="content">'+ str_replyContent +'</div><div class="date-answer">回复时间：'+ str_tempReplyTime +'</div></dd>';
						
						str_html += '<dd class="hide j_replayTextArea"><div><textarea class="txtReplayContent"></textarea></div><div class="buttons"><input type="button" value="取消" onclick="fn_cancelReply(this)" /><input type="button" value="提交" onclick="fn_saveReply(this, '+ n_feedbackId +')" /><input type="button" value="提交并回复" onclick="fn_saveReply(this, '+ n_feedbackId +', \''+ str_email +'\')" /></div>';
						
						arr_tableData[i] = [str_html];	
						break;
				}
			}
		}
		// 是否显示统计图
		if ( str_who == 'battery' ) { // 电量查询的标题
			var n_len =  n_searchLen-1;
			
			arr_graphic_x[0] = obj_reaData[0].battery_time;
			arr_graphic_x[n_len] = obj_reaData[n_len].battery_time;
			obj_chart = {'name': $('#terminal_num').val(), 'data': arr_graphic};
			
			// 电量查询 显示
			$('#battery_chart_link').unbind('click').bind('click', function() {
				var n_dialogWidth = $(window).width() - 300
				/**
				* 电量查询 : 统计图事件
				*/
				if ( n_dialogWidth < 800 ) {
					n_dialogWidth = 830;
				}
				obj_chartDialog.dialog({
					autoOpen: true,
					width: n_dialogWidth,
					height: 480,
					position: [10, 60],
					resizable: false,	// 不可变大小
					modal: true
				});
				fn_initChart([obj_chart], arr_graphic_x, arr_categories, str_container, str_unit, str_who);	// 初始化chart图
			}).show();
		}
	}
	
	obj_searchDataTables.fnClearTable(); //清除dataTables数据
	fn_initDataTables('search_table', str_who, arr_tableData);
	$('#search_table').css('width', '100%');
}
/**
* 
*/
function fn_initDataTables(str_tableName, str_who, obj_tableData) {
	var arr_ableTitle = ''; // 查询结果的结果头
	
	if ( str_who == 'battery' ) {
		arr_ableTitle = [
			{ 'sTitle': '时间' },
			{ 'sTitle': '电量' }
		];
	} else if ( str_who == 'log' ) { // 报文查询的标题
		arr_ableTitle = [
			{ 'sTitle': '时间' },
			{ 'sTitle': '服务名称' },
			{ 'sTitle': '消息类别' },
			{ 'sTitle': '消息内容', 'sClass': 'table_left_class' },
			{ 'sTitle': '显示详细' }
		];
	} else if ( str_who == 'packet' ) { //日志查询的标题
		arr_ableTitle = [
			{ 'sTitle': '时间' },
			{ 'sTitle': '报文类型' },
			{ 'sTitle': '报文内容', 'sClass': 'table_left_class' }
		];	
	} else if ( str_who == 'feedback' ) {	// 意见反馈
		arr_ableTitle = [
			{
				'sTitle': '意见反馈'
			}
		];
	}
	obj_searchDataTables = $('#'+str_tableName).dataTable({
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
		},
		'aaData': obj_tableData, // 显示的数据
        'aoColumns': arr_ableTitle, // 结果头
		'fnInitComplete': function(oSettings, json) {
			$('#'+str_tableName+' tr').hover(function(){
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

/*
* 检测 所有的类型是否被选中
*/
function fn_validPacketTypeCheck() {
	var obj_packetType = $('#packetTypes input[name=packet_type]'),
		n_packetLen = obj_packetType.length, 
		n_packetCount = 0;
	
	obj_packetType.each(function(e) {
		var str_checked = $(this).attr('checked'),
			str_check_type = $(this).val();
		
		if ( str_checked ) { 
			n_packetCount++;
		}
	});
	if ( n_packetCount == n_packetLen ) {
		return true;
	} 
	return false;	
}

/**
* 初始化 统计图
*/
function fn_initChart(arr_series, arr_graphic_x, arr_categories, str_container, str_unit, str_who) {
	var str_title = arr_series[0].name +'电量统计图';
	
	// 初始化统计图对象
	chart = new Highcharts.Chart({
		chart: {
			renderTo: str_container,
			type: 'line',
			marginRight: 30
		},
		title: {
			text: str_title,
			style: {
				margin: '10px 100px 0 0' // center it
			}
		},
		xAxis: {
			categories: arr_graphic_x,
			title: {
				text: '时间'
			}
		},
		yAxis: {
			min: 0,                
			allowDecimals: false,
			title: {
				text: '电量值('+ str_unit +')'
			},
			plotLines: [{
				value: 0,
				width: 1,
				color: '#808080'
			}]
		},
		credits: { // 去版权信息
			enabled: false
		},
		tooltip: {
			formatter: function(e) { 
					return '<b>'+ this.series.name +'</b><br/>时间: '+
					arr_categories[this.point.x]+', 电量: '+ this.y + str_unit;
			}
		},
		series: arr_series
	});
}

/**
* 编辑回复
*/
function fn_editReply(obj_tempThis) {
	var obj_this = $(obj_tempThis),
		obj_answer = obj_this.parent().parent().siblings('.j_answer'),
		obj_replyContent = obj_answer.children('.j_replyContent'),
		obj_dt = obj_answer.children('dt'),
		obj_textareaDiv = obj_answer.children('.j_replayTextArea'),
		obj_textarea = obj_textareaDiv.find('textarea');
	
	obj_dt.show();
	obj_replyContent.hide();	// 显示或隐藏回复内容
	obj_textarea.val(obj_replyContent.children('.content').html());
	obj_textareaDiv.show();	// 显示或隐藏回复框	
}

/**
* 回复邮件
* str_email：联系人email
* str_content：回复的内容

function fn_replyEmail(obj_tempThis, str_email) {
	if ( str_email != '' ) {
		var obj_params = {'contact': str_email, 'content': ''},
			obj_this = $(obj_tempThis),
			str_content = obj_this.parent().parent().siblings('.j_answer').find('.content').html();
				
		if ( str_content != '' ) {
			obj_params.content = str_content;
			if ( confirm('确定要将客服回复内容发送给”' + str_email + '”吗？' ) ) {		
				$.post_('/mail', JSON.stringify(obj_params), function(data) {
					if ( data.status == 0 ) {
						alert('邮件已发送。');
					} else {
						alert('邮件回复错误，请稍后再试。');
						return;
					}
				});
			}
		} else {
			alert('请先填写回复内容。');
			return;
		}
	}
}*/

/**
* 保存回复
* obj_tempThis: 要操作的对象
* id：编辑记录ID
*/
function fn_saveReply(obj_tempThis, id, str_email) {
	var obj_this = $(obj_tempThis),
		obj_textareaDiv = obj_this.parent().parent(),
		obj_user = obj_textareaDiv.parent().siblings('.user'),
		obj_replyContent = obj_textareaDiv.siblings('.j_replyContent'),
		obj_dt = obj_textareaDiv.siblings('dt'),
		obj_textarea = obj_textareaDiv.find('textarea'),
		str_val = obj_textarea.val(),
		obj_params = {'reply': '', 'id': id},
		obj_msg = $('#sendEmailMsg'),
		n_timeout = 200;
		
	if ( str_val != '' ) {
		obj_params.reply = str_val;
		if ( str_email ) {	// 提交并回复
			obj_params.email = str_email;
		}
		$.put_('/feedback', JSON.stringify(obj_params), function(data) {
			if ( str_email ) {
				fn_lockScreen('正在发送中...');
				n_timeout = 2000;
			}
			if ( data.status == 0 ) {
				setTimeout(function() {
					obj_replyContent.children('.content').html(str_val);
					obj_replyContent.children('.date-answer').html(fn_changeNumToDateString(data.reply_time));
					obj_replyContent.show();
					obj_dt.css('display', 'inline');
					obj_textareaDiv.hide();
					if ( str_email ) {	// 未回复 ---> 已修复
						obj_user.find('font').attr('class', '').addClass('green').html('已修复');
						
						$('#layerMsgContent').html('发送成功。');
						setTimeout(function() {
							fn_unLockScreen();
						}, 1000);
					} else {
						alert('回复成功。');
					}
				}, n_timeout);
			} else {
				$('#layerMsgContent').html('回复失败，请稍后再试。');
				setTimeout(function() {
					fn_unLockScreen();
				}, 1000);
				return;
			}
		});
	} else {
		alert('回复内容不可为空。');
		return;
	}
}

/**
* 取消回复
* obj_tempThis: 要操作的对象
*/
function fn_cancelReply(obj_tempThis) {
	var obj_this = $(obj_tempThis),
		obj_textareaDiv = obj_this.parent().parent(),
		obj_user = obj_textareaDiv.parent().siblings('.user'),
		obj_replyContent = obj_textareaDiv.siblings('.j_replyContent'),
		obj_dt = obj_textareaDiv.siblings('dt'),
		obj_content = obj_replyContent.children('.content');

	if ( !obj_content.html() ) {
		obj_dt.css('display', 'none');
	}
	obj_textareaDiv.hide();
	obj_replyContent.show();
}

/**
* 删除反馈
* id：删除记录ID
*/
function fn_deleteFeedback(id) {
	if ( confirm('确定要删除该意见反馈吗？') ) {
		$.delete_('/feedback'+'?ids=' + id, '', function(data) {
			if ( data.status == 0 ) {
				var pos = obj_searchDataTables.fnGetPosition($("#item" + id).parent().parent()[0]);
							
				obj_searchDataTables.fnDeleteRow(pos);
				alert('删除成功。');
			} else {
				alert('删除失败，请稍后再试。');
				return;
			}
		});
	}
}