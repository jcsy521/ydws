//用来判断集团的选择

//用来判断集团的选择
var groupNum = 'yes';
function clickGroup() {
	if (groupNum == 'yes') {
			fn_loadSchool();
			groupNum = 'no';			
		} else {
			return;
		}
}
function fn_changeSchool() {
	var selectCityId = $('#cities').val(); // 选中的option value
	$('#citiesId').val(selectCityId); // 填充到hidden
	fn_loadSchool();
}
function fn_loadSchool () {
	var citiesId = $('#citiesId').val(), // 选中的cityid
		group = $('#corps'),
		cityTemp = [],
		typeTemp = [], // 集团
		type = $('#type').val();
	if ( citiesId != '0' && citiesId != '') { // 如果有选择城市的话 加载集团信息
		cityTemp[0] = parseInt(citiesId, 10);
		var element = parent.document.getElementById('cacheDatas'), // 外层数据
			str_groupVal = '';
		if ( $(element).children().length > 0 ) {
			str_groupVal = $(element).children('li[id=group]').first().html(); // 保存的group的值
		}
		$.get('/corplist', '', function (data) {
			group.empty();
			var groupHtml = '';
			if (data && data.length > 0) {
				groupHtml = '<option value="0">--请选择集团--</option>';
				for (var i = 0; i < data.length; i++) {
					if ( data[i].id == parseInt(str_groupVal) ) { // select 被选中
						groupHtml += '<option value="' +data[i].id+ '" selected="selected">' +data[i].name+ '</option>';
					} else {
						groupHtml += '<option value="' +data[i].id+ '">' +data[i].name+ '</option>';
					}
				}
			} else {
				groupHtml += '<option value="0">-------暂无集团-------</option>';
			}
			group.html(groupHtml);
			pd = null;
		});
	}
}
// group init
function fn_initGroup() {
	groupNum = 'yes';
	$('#group').html('<option value="0">--请选择集团--</option>');
}

/*
* 用户业务变更 
* 个人->集团  or 集团 ->个人
*/ 
function bus_changeUserType(str_ecName, str_tMobile) {
	// 新增初始化dialog
	$('#userTypeChangeDialog').dialog({
		autoOpen: false,
		height: 200,
		width: 300,
		position: [300, 100],
		modal: true,
		resizable: false,
		close: function(e, ui) {
			$('#changeUserType_input').autocomplete('close');
		}
	});
	$('#txt_changeTmobile').html(str_tMobile);
	$('#userTypeChangeDialog').attr('title', '业务变更').dialog('option', 'title', '业务变更').dialog( "open" );
	$('#changeUserType_corpName').hide();
	
	if ( str_ecName == '' ) {// 如果是个人切集团
		$('#changeUserType_corpName').show();
		// 提取集团数据
		var obj_corpSelect = $('#corps_select option'),
			arr_autoCorpsData = [],
			n_corpSelectOptions = $('#corps_select option').length,
			obj_corpsSearch = $('#changeUserType_input');
			
		if ( n_corpSelectOptions > 0 ) {
			//获取集团数据
			obj_corpSelect.each(function(e) {
				var str_corpName = $(this).html(),
					str_ecId = $(this).attr('value');
				
				if ( str_corpName != '全部' ) {
					arr_autoCorpsData.push({'label': str_corpName, 'value': str_ecId});
				}
			});
			// 集团下拉框图标事件	
			$('#changeUserType_sign').unbind('click').click(function(e) {
				var b_autoCompleteSt = $('.ui-autocomplete').is(':visible');
				
				if ( b_autoCompleteSt ) {
					obj_corpsSearch.autocomplete('close');
				} else {
					obj_corpsSearch.autocomplete('search', '');
				}
			});
			fn_initAutoUserTypeChange(arr_autoCorpsData);
			
			var str_fstVal = arr_autoCorpsData[0].label
				str_fstEcid = arr_autoCorpsData[0].value;
			
			obj_corpsSearch.val(str_fstVal);
			$('#changeUserType_hidden').val(str_fstEcid);
		}
	}
	// 变更保存
	$('#changUserTypeSave').unbind('click').click(function(e) {
		var obj_postData = {};
		
		if ( str_ecName == '' ) {
			obj_postData = {'cid': $('#changeUserType_hidden').val(), 'tmobile': str_tMobile};
		} else {
			obj_postData = {'tmobile': str_tMobile};
		}
		
		$.post('/usertype',  JSON.stringify(obj_postData), function (data) {
			if ( data.status == 0 ) {
				alert('操作成功，请重新查询！');
				$('#userTypeChangeDialog').dialog('close');
			} else {
				alert(data.message);
			}
		});
	});
}

/**
* 初始化短信接收号码的autocomplete
*/
function fn_initAutoUserTypeChange(arr_autoCorpsData) {
	var obj_compelete = $('#changeUserType_input');
	
	// autocomplete	自动完成 初始化
	obj_compelete.autocomplete({
		minLength: 0,
		source: arr_autoCorpsData,
		select: function(event, ui) {			
			var obj_item = ui.item,
				str_tLabel = obj_item.label,
				str_tVal = obj_item.value;
			
			$('#changeUserType_hidden').val(str_tVal);
			obj_compelete.val(str_tLabel);
			return false;
		}
	});
}