/*
    *人员编辑页面
    *该人选择的省份、城市
    *都是通过后台直接下发到html上
    *然后再由js到html上获得数据
    *在重新填会到html和dialog上
*/
function f_editAdmin(data, privi_data) {
    f_forEditAdmin(data.provinces, '#provincesNames');
    f_forEditAdmin(data.cities, '#citiesNames');
}
function f_forEditAdmin(data, output) {
    if (data && (data.length > 0)) {
        var strings = '', len = data.length;
        if (output == '#provincesNames') {
            for (var i = 0; i < len; i++) {
                strings += data[i].name + '+';
                _getProvinceIdString += data[i].id + ',';
            }
            var sPid = _getProvinceIdString;
            sPid = sPid.substr(1, sPid.length - 2);
            $('#provincesId').val(sPid);
        } else {
            for (var i = 0; i < len; i++) {
                strings += data[i].name + '+';
                _getCityIdString += data[i].id + ',';
                _getProvinceIdString += data[i].province_id + ','
            }
            /*
                *将该用户所选择的省、市数据
                *生成代码到div上
                *用于当用户在人员编辑页面
                *不重新修改省、市时。就将其
                *原本的数据提交到后台
            */
            $('#d_cities').html(
                f_forMakeCheckBoxHtml(data,"cities",'"getSchools"','_ajaxGetData',data[0].province_id)
            );
            var sCid = _getCityIdString;
            sCid = sCid.substr(1, sCid.length - 2);
            $('#citiesId').val(sCid);
            $('#d_cities>ul').hide();
        }
        strings = strings.substr(0, strings.length - 1);
        $(output).val(strings);
    }    
}
//删除用户
function adminDelete(adminid) {
    var pos = oTable.fnGetPosition(document.getElementById("admin" + adminid));
	$.post('/administrator/delete/' + adminid, function (data) {
		if (data.success == 0) {
            oTable.fnDeleteRow(pos);
		} else {
			alert("您没有删除自己账号的权限！");
		}
	});
}
// stop business 
function businessStop(tmobile, seq, tempType) {
	var obj_service_status = $('#service_status' + seq ),
		status = obj_service_status.attr('service_status'),
		str_status = status == '0' ? '1' : '0',
		str_html = status == '0' ? '停用' : '启用',
		str_msg = '', 
		str_url = '/business/service/' + tmobile + '/' + str_status;
	
	if ( status == '0' ) {
		str_msg = '是否启用该用户？';
	} else {
		str_msg = '是否停用该用户？';
	}
	if ( tempType == 'ec' ) {
		str_url = '/ecbusiness/service/' + tmobile + '/' + str_status;
	}
	
	if ( confirm(str_msg) ) {
		$.post(str_url, function (data) {
			if ( data.success == 0 ) {
				obj_service_status.attr('service_status', str_status);
				obj_service_status.html(str_html);
			} else {
				alert("操作失败！");
			}
		});
	}
}
// delete business 
function businessDelete(tmobile, mobile, tempType) {
	var str_id = 'business' + tmobile, 
		str_url = '/business/delete/' + tmobile + '/' + mobile, 
		str_msg = '是否删除该用户？';
		
	if ( tempType == 'ec' ) {
		str_id = 'ecbusiness' + tmobile, 
		str_url = '/ecbusiness/delete/' + tmobile;
		str_msg = '是否删除该集团？';
		// 判断要删除的集团下是否还有终端 ,如果有则不能进行集团删除 并提示
		var n_ecTerminals = parseInt($('#ec'+tmobile).html());
		
		if ( n_ecTerminals != 0) {
			alert('该集团下有终端，无法删除集团！');
			return;
		}
	}
	var obj_pos = oTable.fnGetPosition(document.getElementById(str_id));
	
	if ( confirm(str_msg) ) {
		fn_lockScreen('删除操作进行中...');
		$.post(str_url, function (data) {
			fn_unLockScreen();
			if ( data.success == 0 ) {
				oTable.fnDeleteRow(obj_pos);
			} else {
				alert("删除失败。");
			}
		});
	}
}
// 短信重发
function fn_smsReset(tmobile, mobile, obj_panel) {
	var obj_data = {
		'tmobile': tmobile, 
		'pmobile': mobile
	};
	
	$.post('/sms/register', JSON.stringify(obj_data), function (data) {
		if ( data.success == 0 ) {
			$(obj_panel).parent().html('短信已发送').removeClass().addClass('sms_status1');
		}
	});
}