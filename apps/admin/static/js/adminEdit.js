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
        var strings = "", len = data.length;
        if (output == '#provincesNames') {
            for (var i = 0; i < len; i++) {
                strings += data[i].name + "+";
                _getProvinceIdString += data[i].id + ',';
            }
            var sPid = _getProvinceIdString;
            sPid = sPid.substr(1, sPid.length - 2);
            $('#provincesId').val(sPid);
        } else {
            for (var i = 0; i < len; i++) {
                strings += data[i].name + "+";
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
	$.post("/administrator/delete/" + adminid, function (data) {
		if (data.success == 0) {
            oTable.fnDeleteRow(pos);
		} else {
			alert("您没有删除自己账号的权限！");
		}
	});
}
// delete business 
function businessDelete(tmobile, status) {
	var pos = oTable.fnGetPosition(document.getElementById("business" + tmobile)),
		str_status = status == '0' ? '1' : '0';
	$.post("/business/delete/" + tmobile + "/" + str_status, function (data) {
		if (data.success == 0) {
            oTable.fnDeleteRow(pos);
		} else {
			alert("删除失败。");
		}
	});
}
