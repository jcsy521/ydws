// 操作员保存
window.dlf.fn_saveOperator = function() {
	var	str_id = $('#hidOperatorId').val(),
		arr_groups = $('#operatorGroups input:checked'),// $('#txt_operatorGroup').val(),
		str_groupIds = '',
		str_name = $('#txt_operatorName').val(),
		str_mobile = $('#txt_operatorMobile').val(),
		str_address = $.trim($('#txt_operatorAddress').val()),
		str_email = $('#txt_operatorEmail').val(),
		obj_operatorData = {'id': '', 'group_id': str_groupIds, 'name': str_name, 'mobile': str_mobile, 'address': str_address, 'email': str_email},
		obj_header = $('#operatorTableHeader'),
		b_header = obj_header.is(':hidden');

	// kjj add in 2013-08-05 分组id 
	for ( var x = 0 ;x < arr_groups.length; x++ ) {
		var obj_group = $(arr_groups[x]);
		
		str_groupIds += obj_group.attr('groupId') + ',';
	}
	if ( str_groupIds != '' ) {
		str_groupIds = str_groupIds.substr(0, str_groupIds.length-1);
	}
	obj_operatorData.group_id = str_groupIds;
	if ( str_id ) {
		if ( b_header ) {	// 判断表头是否显示
			obj_header.show();
		}
		obj_operatorData.id = parseInt(str_id);
		dlf.fn_jsonPut(OPERATOR_URL, obj_operatorData, 'operator', '操作员数据保存中');
	} else {
		dlf.fn_jsonPost(OPERATOR_URL, obj_operatorData, 'operator', '操作员数据保存中');
	}
}
/**
* 编辑操作员
*/
window.dlf.fn_editOperator = function(n_id) {
	dlf.fn_onInputBlur();	// 操作员手机号事件侦听
	$('#addOperatorForm input').css('color', '#000000');
	if ( n_id ) {
			var obj_currentOperatorItem = $('#operatorTable tr[id='+ n_id +']'), 
				obj_currentOperatorItemTds = obj_currentOperatorItem.children(), 
				str_currentGroupIds = $(obj_currentOperatorItemTds.eq(0)).attr('groupId'),
				str_currentName = $(obj_currentOperatorItemTds.eq(1)).html(),
				str_currentMobile = $(obj_currentOperatorItemTds.eq(2)).html(),
				str_currentAddress = $(obj_currentOperatorItemTds.eq(3)).attr('title'),
				str_currentEmail = $(obj_currentOperatorItemTds.eq(4)).attr('title');
			
			$('#hidOperatorId').val(n_id);
			$('#hidOperatorMobile').val('');
			$('#txt_operatorName').val(str_currentName);
			$('#txt_operatorMobile').val(str_currentMobile).data('oldmobile', str_currentMobile);
			$('#txt_operatorAddress').val(str_currentAddress);
			$('#txt_operatorEmail').val(str_currentEmail);
			fn_getGroupData();	//初始化分组
			
			if ( str_currentGroupIds.search(',') != -1 ) {
				var arr_groupIds = str_currentGroupIds.split(',');
				
				for ( var i = 0; i < arr_groupIds.length; i++ ) {
					$('#operatorGroups input[groupId='+ arr_groupIds[i] +']').attr('checked', true);
				}
			} else {
				$('#operatorGroups input[groupId='+ str_currentGroupIds +']').attr('checked', true);
			}
			
			$('#addOperatorDialog').dialog('open').dialog('option', 'title', '编辑操作员');
	}
}

/**
* 删除操作员
*/
window.dlf.fn_deleteOperator = function(n_id) {
	if ( n_id ) {
		if ( confirm('确定要删除该操作员吗？') ) {
			$.delete_(OPERATOR_URL+'?ids='+n_id, '', function(data) {
				if ( data.status == 0 ) {
					$('#operatorTable tr[id='+ n_id +']').remove();
					var n_trNum = $('#operatorTable tr').length;
					
					n_dwRecordPageCnt = -1;
					n_dwRecordPageNum = 0;
					dlf.fn_searchData('operator');
				} else {
					dlf.fn_jNotifyMessage(data.message, 'message', false, 3000);
					return;
				}
			});
		}
	}
}
/*
* 操作员获取组信息
* str_operation: add：新增操作员操作
*/
function fn_getGroupData(str_operation) {
	var str_groupSelect = '',
		str_groupId = '',
		obj_operatorGroup = $('#operatorGroups');
	
	$('.j_group').children('a').each(function(e){
		var str_title = $(this).attr('title'),
			str_tempTitle = str_title,
			str_tempGid = $(this).attr('groupid');
		
		if ( str_title.length > 8 ) {
			str_tempTitle = str_title.substr(0, 8) + '...';
		}
		if ( str_title == '默认组' ) {
			str_groupId = str_tempGid;
		}
		// str_groupSelect += '<option value="' +str_tempGid+ '">' +str_tempTitle+ '</option>';
		str_groupSelect += '<li><input type="checkbox" id="chkGroup'+ str_tempGid +'" name="chkGroup" groupId="'+ str_tempGid +'" value="'+  str_tempGid+'" /><label for="chkGroup' + str_tempGid + '"  title="'+ str_title +'">'+ str_tempTitle + '</label></li>';
	});
	obj_operatorGroup.html(str_groupSelect);
	if ( str_operation == 'add' ) {
		$('#operatorGroups input[groupId='+ str_groupId +']').attr('checked', true);
	}
	return str_groupSelect;
}



