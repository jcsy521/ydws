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
	};
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
		$('#packetTypes input[name=packet_type], #packet_all_type').removeAttr('checked');
		
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
				str_mobile = $('#mobile').val(), 
				str_message_type = ''; 
				
			if ( !fn_validMobile(str_mobile) ) {
				return;
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
				'mobile': str_mobile,
				'packet_types': '('+str_message_type+')'
			};
			str_getDataUrl = '/packet';
			
			break;
		case 'battery': //  电量查询
			
			var str_stTime = $('#beginDate').val(), 
				str_entTime = $('#endDate').val(), 
				str_mobile = $('#mobile').val();
				
			if ( !fn_validMobile(str_mobile) ) {
				return;
			}
				
			if ( !fn_validSearchDate() ) {
				return;
			}	
			obj_conditionData = {
				'start_time': fn_changeDateStringToFormat(str_stTime),
				'end_time': fn_changeDateStringToFormat(str_entTime),
				'mobile': str_mobile
			};
			str_getDataUrl = '/battery';
			
			$('#battery_chart_link').hide();
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
		
		if ( str_who == 'log' ) { //日志查询
			arr_recordData = obj_resdata.log_list;
		} else if ( str_who == 'packet' ) { //报文查询
			arr_recordData = obj_resdata.packet_list;
		} else if ( str_who == 'battery' ) { //电量查询
			arr_recordData = obj_resdata.battery_list;
		}
		
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
				}
			}
		}
		// 是否显示统计图
		if ( str_who == 'battery' ) { // 电量查询的标题
			var n_len =  n_searchLen-1;
			
			arr_graphic_x[0] = obj_reaData[0].battery_time;
			arr_graphic_x[n_len] = obj_reaData[n_len].battery_time;
			obj_chart = {'name': $('#mobile').val(), 'data': arr_graphic};
			
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
	};
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
        'aoColumns': arr_ableTitle // 结果头
	});
	$('#'+str_tableName+' tr').hover(function(){
		$(this).children().css({
			'background-color' : '#87CEFF'
		});
	},
	function(){
		$(this).children().removeAttr('style');
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
					marginRight: 30,
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
				tooltip: {
					formatter: function(e) { 
							return '<b>'+ this.series.name +'</b><br/>时间: '+
							arr_categories[this.point.x]+', 电量: '+ this.y + str_unit;
					}
				},
				series: arr_series
			});
	$('svg text').last().remove();	// 移除 网址
}