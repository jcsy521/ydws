var oTable,
	rTable,
	sTable,
	binglogTable,
	tlocationTable;
$(function () {
	oTable = $('#rDataTables').dataTable({
		"bScrollCollapse": true,
		'aaSorting':[], // 默认不排序
		"bJQueryUI": true,
		"bProcessing": true,
		"sPaginationType": "full_numbers",
		"oLanguage": {
		    "sUrl":"/static/js/dataTables.zh_CN.txt"
	    }
	});
	$('#rDataTables tr').hover(function(){
        $(this).children().css({
            'background-color' : '#87CEFF'
        });
    },
    function(){
        $(this).children().removeAttr('style');
    });
	// 集团业务统计
	rTable = $('#reportDataTables').dataTable({
		"bScrollCollapse": true,
		'aaSorting':[], // 默认不排序
		"bJQueryUI": true,
		"bProcessing": true,
		"sPaginationType": "full_numbers",  
		"aLengthMenu": [10, 20, 50, 100], //每页显示可调
		"iDisplayLength":20,//默认每页10条记录
		"oLanguage": {
			"sUrl":"/static/js/dataTables.zh_CN.txt"
		}
	});
	$('#reportDataTables tr').hover(function(){
		$(this).children().css({
			'background-color' : '#87CEFF'
		});
	},
	function(){
		$(this).children().removeAttr('style');
	});

	// 报表统计
	sTable = $('#staticsTables').dataTable({
		"bScrollCollapse": true,
		'aaSorting':[], // 默认不排序
		"bJQueryUI": true,
		"bProcessing": true,
		"sPaginationType": "full_numbers",  
		"aLengthMenu": [10, 15, 20, 50, 100], //每页显示可调
		"iDisplayLength": 15,//默认每页10条记录
		"oLanguage": {
			"sUrl":"/static/js/dataTables.zh_CN.txt"
		}
	});
	$('#staticsTables tr').hover(function(){
		$(this).children().css({
			'background-color' : '#87CEFF'
		});
	},
	function(){
		$(this).children().removeAttr('style');
	});
	// 终端绑定记录查询
	binglogTable = $('#tbindlogDataTables').dataTable({
		"bScrollCollapse": true,
		'aaSorting':[], // 默认不排序
		"bJQueryUI": true,
		"bProcessing": true,
		"sPaginationType": "full_numbers",  
		"aLengthMenu": [10, 20, 50, 100], //每页显示可调
		"iDisplayLength":20,//默认每页10条记录
		"oLanguage": {
			"sUrl":"/static/js/dataTables.zh_CN.txt"
		}
	});
	$('#tbindlogDataTables tr').hover(function(){
		$(this).children().css({
			'background-color' : '#87CEFF'
		});
	},
	function(){
		$(this).children().removeAttr('style');
	});
	// 终端位置查询
	tlocationTable = $('#tlocationDataTables').dataTable({
		"bScrollCollapse": true,
		'aaSorting':[], // 默认不排序
		"bJQueryUI": true,
		"bProcessing": true,
		"sPaginationType": "full_numbers",  
		"aLengthMenu": [10, 20, 50, 100], //每页显示可调
		"iDisplayLength":20,//默认每页10条记录
		"oLanguage": {
			"sUrl":"/static/js/dataTables.zh_CN.txt"
		}
	});
	$('#tlocationDataTables tr').hover(function(){
		$(this).children().css({
			'background-color' : '#87CEFF'
		});
	},
	function(){
		$(this).children().removeAttr('style');
	});
});