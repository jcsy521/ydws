/**
* KJJ add in 2014.04.30
* 网页导出excel表方法
* 兼容IE，chrome等浏览器
*/

/**
* 导出excel 方法
* str_excelName: excel 表名称
*/
function fn_exportExcel(str_excelName) {
	var obj_delayLink = $('#exportDelay');
	
	if( navigator.appName == "Microsoft Internet Explorer" ) {
		obj_delayLink.unbind('click').click(function() {
			fn_tableToExcelFromIE('tempDelayTable',null, str_excelName);
		});		
	} else {
		fn_tableToExcel('tempDelayTable', '停留点列表');
		//obj_delayLink.attr('href', fn_tableToExcel('tempDelayTable', '停留点列表'));
	}
}

/**
* IE导出方法
* 读取表格中每个单元到EXCEL中
*/
function fn_tableToExcelFromIE(inTblId, inWindow, str_excelName) { 
	try { 
		var allStr = "",
			curStr = "",
			fileName = str_excelName + '.csv';	// getExcelFileName();
		
		if ( inTblId != null && inTblId != '' && inTblId != 'null' ) { 
			curStr = getTblData(inTblId, inWindow); 
		}
		if (curStr != null) { 
			allStr += curStr; 
		} else { 
			alert("你要导出的表不存在！"); 
			return; 
		}
		doFileExport(fileName, allStr); 
	} catch(e) {
		alert("导出发生异常:" + e.name + "->" + e.description + "!"); 
	}
}

/**
* 遍历页面上的table获取数据
*/
function getTblData(inTbl, inWindow) { 
	var rows = 0; 
	//alert("getTblData is " + inWindow); 
	var tblDocument = document; 
	if (!!inWindow && inWindow != "") { 
		if (!document.all(inWindow)) { 
			return null; 
		}
		else { 
			tblDocument = eval(inWindow).document; 
		} 
	} 
	var curTbl = tblDocument.getElementById(inTbl); 
	var outStr = ""; 
	if (curTbl != null) { 
		for (var j = 0; j < curTbl.rows.length; j++) {
			for (var i = 0; i < curTbl.rows[j].cells.length; i++) {
				if (i == 0 && rows > 0) { 
					outStr += " \t"; 
					rows -= 1; 
				}
				outStr += curTbl.rows[j].cells[i].innerText + "\t"; 
				if (curTbl.rows[j].cells[i].colSpan > 1) { 
					for (var k = 0; k < curTbl.rows[j].cells[i].colSpan - 1; k++) { 
						outStr += " \t"; 
					} 
				} 
				if (i == 0) { 
					if (rows == 0 && curTbl.rows[j].cells[i].rowSpan > 1) { 
						rows = curTbl.rows[j].cells[i].rowSpan - 1; 
					} 
				} 
			} 
			outStr += "\r\n"; 
		}
	} else { 
		outStr = null; 
		alert(inTbl + "不存在!"); 
	}
	return outStr; 
}

/**
* IE 浏览器下导出excel文件
*/
function doFileExport(inName, inStr) { 
	var xlsWin = null; 
	if (!!document.all("glbHideFrm")) { 
		xlsWin = glbHideFrm; 
	} else { 
		var width = 6; 
		var height = 4; 
		var openPara = "left=" + (window.screen.width / 2 - width / 2) 
				+ ",top=" + (window.screen.height / 2 - height / 2) 
				+ ",scrollbars=no,width=" + width + ",height=" + height; 
		xlsWin = window.open("", "_blank", openPara); 
	}
	xlsWin.document.write(inStr); 
	xlsWin.document.close(); 
	xlsWin.document.execCommand('saveAs', true, inName); 
	xlsWin.close(); 
}

/**
* 导出数据 非IE
*/
function fn_tableToExcel(table, name) {
	var uri = 'data:application/vnd.ms-excel;base64,', 
	template = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40"><head><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>{worksheet}</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]--></head><body><table>{table}</table></body></html>'
    , base64 = function(s) { return window.btoa(unescape(encodeURIComponent(s))) }
    , format = function(s, c) { return s.replace(/{(\w+)}/g, function(m, p) { return c[p]; }) }
	
	var str_tableHtml = $('#tempDelayTable').html();
	
	var ctx = {worksheet: name || 'Worksheet', table: str_tableHtml},
		str_url = uri + base64(format(template, ctx));
	
	$('#exportDelay').attr('href', str_url);
}