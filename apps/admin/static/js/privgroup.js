//to get the privgroup detail for display
function toPrivDetail(privID, privNAME) {
	var privHTML = "<h3>" + privNAME + "的详细权限</h3><table class='tableStyle'><tr><td class='tLeft'>具体权限</td><td align='left'><ul>";
	$.getJSON('/privileges/' + privID, function(data) {
		for (var i = 0; i < data.length; i++) {
			privHTML += '<li>' + data[i].name + "</li>";
		}
		privHTML += "</ul></td></tr></table>";
		$("#privList").html(privHTML);
	});
}

//resetClick
function resetClick() {
	$(":checkbox").each(function() {
		if ($(this).attr('checked') == true) {
			$(this).attr("checked", false);
		}
	});
}

//当用户点击"重置"时清除验证样式
function toClearFormError() {
	$(".formError").remove();
}

//privlige form
function privgroupSubmit() {
	var arrCheck = $("#formID :checkbox");
	var privs = "";
	for (var i = 0; i < arrCheck.length; i++) {
		if (arrCheck[i].checked) {
			privs = privs + arrCheck[i].value + ","
		}
	}
	privs = privs.substr(0, privs.length - 1);
	if (privs == "") {
		alert("必须为权限组选择一项权限！");
		return false;
	}
	return true;
}

//priv delete
function privDelete(privid) {
	var pos = oTable.fnGetPosition(document.getElementById("priv" + privid));
	$.post("/privgroup/delete/" + privid, function(data) {
		if (data.status == 0) {
			oTable.fnDeleteRow(pos);
		}
	});
}