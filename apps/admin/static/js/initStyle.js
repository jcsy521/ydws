﻿var chart = null; // 统计图对象

$(function() {
	if (window.location.host == 'ajt.zhydgps.com') {
		document.title = '安捷通后台管理系统';
		$('#logo').html('安捷通后台系统 v1.0');
	}
	//将页面查询到的时间进行转换
	var timeta = $(".j_timestamp");
	if (timeta.length != 0) {
		timeta.each(function() {
			$(this).html(toHumanDate($(this).html(), "no"));
		});
	}
	/*
	 *修改 iframe中body的样式
	 */
	if ($('body').find('#left').length == 0) {
		$('body').css({
			'padding': '10px 0px 0px 0px'
		});
	}
	$('input[type=text],input[type=password]').css({
		'width': '120px'
	});
	$('input[type=text]').addClass('text_blur');
	$('input[type=text]').focus(function() {
		$(this).removeClass('text_blur').addClass('text_focus');
	}).blur(function() {
		$(this).removeClass('text_focus').addClass('text_blur');
	});
	$('select').css({
		'width': '120px'
	});
	$('.j_userSelect').css({
		'width': '122px'
	});
	$('#showOrHideSearch').toggle(function() {
		$('#searchTable').show();
		$('#showOrHideSearch').text('-');
	}, function() {
		$('#searchTable').hide();
		$('#showOrHideSearch').text('+');
	});

	$('#provincesNames,#privs').click(function() {
		var pLeft = parent.document.getElementById('left');
		if (pLeft) {
			left = pLeft.clientWidth + 150;
		}
	});

	$('legend').click(function() { // fieldset的样式
		$(this).next("form").slideToggle('slow');
	});

	//添加控件
	$('#start_time1,#end_time1').datepicker();
	$('#start_time1,#end_time1').datepicker('option', 'maxDate', '0d');
	$('#start_time1,#end_time1').datepicker('option', 'setDate', new Date());
	// 日报时间控件 默认昨天
	$('#daily_time').datepicker();
	$('#daily_time').datepicker('option', 'maxDate', '0d');

	// open business date and close date init
	$('#begintime1').datepicker({
		onSelect: function(dateText, inst) { // dateText：当前选中日期  inst: 当前日期插件实例
			$('#endtime1').datepicker('option', 'minDate', dateText); // set minDate is today
		}
	});
	$('#begintime1').datepicker('option', 'minDate', new Date()); // set minDate is today
	$('#endtime1').datepicker('option', 'minDate', new Date()); // set minDate is today
	$('#begintime1, #endtime1').datepicker();

	// 报表统计时间控件

	$('#report #start_time1, #report #end_time1').datepicker('option', 'maxDate', '-1d');
	/*
	 *初始化地图页面的大小
	 *初始化右侧iframe大小
	 */
	var pl = parent.document.getElementById('logo');
	if ($(pl)[0] == undefined) {
		logoHeight = 62;
	} else {
		logoHeight = $(pl)[0].offsetHeight;
	}
	var frameHeight = parent.window.screen.height - logoHeight - 160;
	if ($.browser.msie) {
		frameHeight = parent.window.screen.height - logoHeight - 162;
	} else if (window.google && window.chrome) {
		frameHeight = parent.window.screen.height - logoHeight - 112;
	}
	$('#frameMap').css({
		'height': (frameHeight - 90) + 'px'
	});
	$('#contantIframe').css({
		'height': (frameHeight - 52) + 'px'
	});
	$('.juser_type').click(function() {
		$domRadio = $(this), str_radioVal = $domRadio.val(), $plan = $('.planType');
		if (str_radioVal == 1) { // 家长
			$plan.hide();
			//$('#user_typeTh, #user_typeTd').next().remove();
		} else { // 儿童
			$plan.show();
			//$('#user_typeTh').after('<th class="ui-state-default"><div class="DataTables_sort_wrapper">套餐类型<span class="css_right ui-icon ui-icon-carat-2-n-s"></span></div></th>');
			//$('#user_typeTd').after('<td>{{ user["plan"] }}</td>');
		}
	});

	//当用户点击导出excel按钮时,进行判断是否有记录
	$('#exportData').click(function() {
		if ($('#rDataTables td').length == 1) {
			alert('没有查询记录，无法导出！');
			return false;
		}
	});
	// 业务用户编辑设置车型,及颜色
	var obj_carType = $('#ctype'),
		obj_carColor = $('#carcolor');

	obj_carType.val(obj_carType.attr('cartype'));
	obj_carColor.val(obj_carColor.attr('carcolor'));
	// 统计图的关闭按钮事件绑定
	$('.j_close').click(function() {
		fn_closeWrapper();
	});

	// 短信接收号码的下拉框
	if ($.browser.msie && parseInt($.browser.version) <= 8) {
		$('#corps_sign, #changeUserType_sign').css('top', '0');
	}

	// js模拟select
	var obj_corpsSearch = $('#corps'),
		arr_autoCorpsData = [],
		obj_autoCorpsBakData = [],
		str_selectType = $('#corps_select').attr('selecttype'),
		obj_corpSelect = $('#corps_select option'),
		n_corpSelectOptions = $('#corps_select option').length;

	if (n_corpSelectOptions > 0) {
		if (str_selectType == 'usersearch') {
			obj_corpsSearch = $('#corps_input'),
				str_ecType = obj_corpsSearch.attr('ectype');
			//获取集团数据
			obj_corpSelect.each(function(e) {
				var str_corpName = $(this).html(),
					str_ecId = $(this).attr('value');

				arr_autoCorpsData.push({
					'label': str_corpName,
					'value': str_ecId
				});

				obj_autoCorpsBakData[str_ecId] = {
					'ecname': str_corpName
				};
			});
			obj_corpsSearch.data({
				'corpdata': obj_autoCorpsBakData
			});
			fn_PopData(str_ecType);
		} else {
			//获取集团数据
			obj_corpSelect.each(function(e) {
				var str_corpName = $(this).html(),
					str_ecMobile = $(this).attr('ecmobile'),
					str_ecId = $(this).attr('value');

				arr_autoCorpsData.push({
					'label': str_corpName,
					'value': str_ecId
				});
				obj_autoCorpsBakData[str_ecId] = {
					'ecname': str_corpName,
					'ecmobile': str_ecMobile
				};
			});
			var obj_tempSelectOpts = $($('#corps_select option')[0]);

			obj_corpsSearch.data({
				'corpdata': obj_autoCorpsBakData
			}).attr('ecid', obj_tempSelectOpts.val());
			//obj_corpsSearch.val(arr_autoCorpsData[0].label);
			//$('#ecmobile').val(obj_tempSelectOpts.attr('ecmobile'));

		}
		// 短信接收号码的下拉框事件	
		$('#corps_sign').unbind('click').click(function(e) {
			var b_autoCompleteSt = $('.ui-autocomplete').is(':visible');

			if (b_autoCompleteSt) {
				obj_corpsSearch.autocomplete('close');
			} else {
				obj_corpsSearch.autocomplete('search', '');
			}
		});
		fn_initAutoCorps(arr_autoCorpsData);
	}
});
//to clear the password for message
function clearSpan() {
		var obj = $(".error");
		if (obj) {
			obj.text("");
		}
	}
	// 清除文本输入框中的特殊字符
function fn_textKeyUp(obj_this, str_reg) {
		var $tempInput = $(obj_this),
			str_tempVal = $(obj_this).val();
		if (str_reg == 'text') {
			$tempInput.val(str_tempVal.replace(/[^a-zA-Z0-9\u4e00-\u9fa5\ \_]/g, ''));
		} else if (str_reg == 'user') {
			$tempInput.val(str_tempVal.replace(/[^a-zA-Z0-9\ ]/g, ''));
		} else {
			$tempInput.val(str_tempVal.replace(/[^\d]/g, ''));
		}
	}
	// input string, return a number
function fn_getNumber(str) {
		return str.replace(/\D/g, '');
	}
	// 通过车辆类型标记返回相应的车辆类型文字
function fn_setCarType(n_carType) {
		switch (n_carType) {
			case 1:
				return '小汽车';
				break;
			case 2:
				return '小货车';
				break;
			case 3:
				return '大巴车';
				break;
			case 4:
				return '摩托车';
				break;
			default:
				return '';
				break;
		}
	}
	// 通过车辆颜色编号获取车辆颜色
function fn_setCarColor(n_carColor) {
		switch (n_carColor) {
			case 1:
				return '黑色';
				break;
			case 2:
				return '白色';
				break;
			case 3:
				return '银色';
				break;
			case 4:
				return '红色';
				break;
			case 5:
				return '黄色';
				break;
			case 6:
				return '灰色';
				break;
			case 7:
				return '其他';
				break;
			default:
				return '';
				break;
		}
	}
	/**
	 * 根据类型生成年或月的下拉列表选项
	 * str_type: year or month
	 * str_dataType: year
	 */
function fn_createYearOrMonthOptions(str_type, str_dataType) {
		var obj_date = new Date(),
			n_year = obj_date.getFullYear(),
			n_month = obj_date.getMonth() + 1,
			str_options = '';

		if (str_dataType == 'year') {
			n_month = 12;
		}
		switch (str_type) {
			case 'year':
				for (var x = n_year - 10; x <= n_year; x++) {
					str_options += '<option value=' + x + '>' + x + '年</option>';
				}
				break;
			case 'month':
				for (var x = 1; x <= n_month; x++) {
					str_options += '<option value=' + x + '>' + x + '月</option>';
				}
				break;
		}
		return str_options;
	}
	/*
	 * 初始化统计图数据及事件
	 */
function fn_initChartData() {
		var obj_chart = $('#chartData'),
			obj_bodyData = $('#reportDataTables tbody tr'),
			str_charTitle = $('#lengendTitle').html();
		n_bodyLen = obj_bodyData.length,
			n_count = 0,
			arr_series = [],
			arr_categories = [],
			str_chartTitle = '',
			arr_newCorp = [],
			arr_totalCorp = [],
			arr_newTerminal = [],
			arr_totalTerminal = [];

		for (var i = 0; i < n_bodyLen; i++) {
			var obj_tempTr = $(obj_bodyData[i]).children(),
				obj_newCorps = $(obj_tempTr[1]),
				obj_totalCorps = $(obj_tempTr[2]),
				obj_newTerminals = $(obj_tempTr[3]),
				obj_totalTerminals = $(obj_tempTr[4]);

			arr_newCorp[n_count] = parseInt(obj_newCorps.html());
			arr_totalCorp[n_count] = parseInt(obj_totalCorps.html());
			arr_newTerminal[n_count] = parseInt(obj_newTerminals.html());
			arr_totalTerminal[n_count] = parseInt(obj_totalTerminals.html());
			arr_categories[n_count] = i + 1;
			n_count++;
		}
		arr_series = [{
				name: '新增集团数',
				data: arr_newCorp
			}, {
				name: '总集团数',
				data: arr_totalCorp
			}, {
				name: '新增终端数',
				data: arr_newTerminal
			}, {
				name: '总终端数',
				data: arr_newTerminal
			}

		];

		str_chartTitle = str_charTitle + '统计图';

		fn_xdwInitChart(arr_series, arr_categories, str_chartTitle);
		obj_chart.click(function(event) {
			$('#chartContainerWrapper').show();
		}).show();
	}
	/*
	 *初始化统计图对象
	 */
function fn_xdwInitChart(arr_series, arr_categories, str_chartTitle) {
	chart = new Highcharts.Chart({
		chart: {
			renderTo: 'chartContainerContent',
			defaultSeriesType: 'line'
		},
		title: {
			text: str_chartTitle,
			style: {
				margin: '10px 100px 0 0' // center it
			}
		},
		xAxis: {
			categories: arr_categories,
			title: {
				text: '时间'
			}
		},
		yAxis: {
			title: {
				text: '总数'
			},
			plotLines: [{
				value: 0,
				width: 1,
				color: '#808080'
			}]
		},
		tooltip: {
			formatter: function() {
				return '<b>' + this.series.name + '</b><br/>' +
					this.x + ': ' + this.y;
			}
		},
		series: arr_series
	});
	$('svg text').last().remove(); // 移除 网址 
}

/**
 * 窗口关闭事件
 */
function fn_closeWrapper() {
	$('.wrapper').hide();
}

/**
 * 初始化短信接收号码的autocomplete
 */
function fn_initAutoCorps(arr_autoCorpsData) {
	var obj_compelete = $('#corps'),
		str_selectType = $('#corps_select').attr('selecttype');

	if (str_selectType == 'usersearch') {
		obj_compelete = $('#corps_input');
	}
	// autocomplete	自动完成 初始化
	obj_compelete.autocomplete({
		minLength: 0,
		source: arr_autoCorpsData,
		select: function(event, ui) {
			$('.formError').remove();

			var obj_item = ui.item,
				str_tLabel = obj_item.label,
				str_tVal = obj_item.value,
				obj_autoCorpsBakData = $('#corps').data('corpdata'),
				str_selectType = $('#corps_select').attr('selecttype');

			if (str_selectType == 'usersearch') {
				$('#corps_hidden').val(str_tVal);
			} else {
				$('#ecmobile').val(obj_autoCorpsBakData[str_tVal].ecmobile);
				$('#corps').attr('ecid', str_tVal);
			}
			obj_compelete.val(str_tLabel);

			return false;
		}
	});
}