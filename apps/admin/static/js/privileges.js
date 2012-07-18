/*
    *权限
*/
function f_showAllPrivilegesInPage(data) {
    $('#privis').html(f_forPrivilegesHtml(data, "", "checkbox"));
}
function selectPrivileges(obj,thisOption) {
    $.getJSON('/privileges/' + obj, function (data) {
        _getPrivilegeById(data, $('#s' + obj).text(),thisOption);
    });
}
/*
    *根据权限组的id获取该权限组下的基本权限
*/
function _getPrivilegeById(data, name, id) {
    var html = "<p class='privilegesMsg'><em>" +name+ "</em>所包含的权限为：</p>";
	if (data && (data.length > 0)) {
		var dLength = data.length;
		for (var i = 0; i < dLength; i++){
			html += "<span class='cPrivisItem' id='" + data[i].id + "'>" +data[i].name+ "</span>,";
		}
	}
	html = html.substr(0,html.length-1);
	fn_ForShowMsgBox(html, id);
}
function f_forPrivilegesHtml(data, html, checkbox) {
    html += "<ul class='ulCheckbox'>";
	if (data && (data.length > 0)) {
        var dLength = data.length;
        if (checkbox != "checkbox") {
            for (var i = 0; i < dLength; i++) {
                html += "<li class='cPrivisItem'>"
                + "<strong id='" + "Name" +data[i].id+ "'>" +data[i].name+ "</strong>"
                + "</li>";
            }
        } else {
            for (var i = 0; i < dLength; i++) {
                html += "<li>"
                + "<input type='checkbox' name='privileges' />"
                + "<span id='" + "Name" +data[i].id+ "'>" +data[i].name+ "</span>"
                + "</li>";
            } 
        }
	} else {
	    html += "<li>暂未获得到数据</li>"	
	}
    return html;
}
var msgTimeout = null;
function fn_ForShowMsgBox(html, id) {
    var txt = "<div id='markerWindowtitle' class='cMsgWindow'>" +html+ "</div>",
        obj = $(id);
	clearTimeout(msgTimeout);
	$('#msgBox').hide().html(txt).css({
        'top' : (obj.offset().top)+'px',
        'left': (obj.offset().left+100)+'px'
    }).show();
	
}
function fn_closeMsgBox() {
	msgTimeout = setTimeout(function() { $('#msgBox').hide().children().remove(); }, 1000);
}
