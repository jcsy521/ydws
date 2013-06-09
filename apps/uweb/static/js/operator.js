// 操作员保存
window.dlf.fn_saveOperator = function() {
	var	str_id = $('#hidOperatorId').val(),
		str_groupId = $('#txt_operatorGroup').val(),
		str_groupName = $('#txt_operatorGroup').find('option:selected').text(),
		str_name = $('#txt_operatorName').val(),
		str_mobile = $('#txt_operatorMobile').val(),
		str_address = $('#txt_operatorAddress').val(),
		str_email = $('#txt_operatorEmail').val(),
		obj_operatorData = {'id': '', 'group_id': str_groupId, 'group_name': str_groupName, 'name': str_name, 'mobile': str_mobile, 'address': str_address, 'email': str_email},
		obj_header = $('#operatorTableHeader'),
		b_header = obj_header.is(':hidden');

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
				str_currentGroupId = $(obj_currentOperatorItemTds.eq(0)).attr('groupId'),
				str_currentName = $(obj_currentOperatorItemTds.eq(1)).html(),
				str_currentMobile = $(obj_currentOperatorItemTds.eq(2)).html(),
				str_currentAddress = $(obj_currentOperatorItemTds.eq(3)).html(),
				str_currentEmail = $(obj_currentOperatorItemTds.eq(4)).html();
			
			$('#hidOperatorId').val(n_id);
			$('#hidOperatorMobile').val('');
			$('#txt_operatorName').val(str_currentName);
			$('#txt_operatorMobile').val(str_currentMobile).data('oldmobile', str_currentMobile);
			$('#txt_operatorAddress').val(str_currentAddress);
			$('#txt_operatorEmail').val(str_currentEmail);
			$('#txt_operatorGroup').html(fn_getGroupData());
			$('#txt_operatorGroup').val(str_currentGroupId); 
			
		$('#addOperatorDialog').dialog('open').attr('title', '编辑操作员').dialog('option', 'title', '编辑操作员');
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
					
					if ( n_trNum == 1 ) {
						n_dwRecordPageNum = 0;
						dlf.fn_searchData('operator');
					}
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
*/
function fn_getGroupData() {
	var str_groupSelect = '';
	
	$('.j_group').children('a').each(function(e){
		var str_tempTitle= $(this).attr('title'),
			str_tempGid = $(this).attr('groupid');
		str_groupSelect += '<option value="' +str_tempGid+ '">' +str_tempTitle+ '</option>';
	});
	return str_groupSelect;
}



