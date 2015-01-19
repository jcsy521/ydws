function get_request() {
    /* Composer the whole request body.
     */
    // 初始化数据   
    var tid = $('#tid').val();
    var s_type = $('#s_type').val();
    var category = $('#category').val();
    var body = {
        's_type': s_type,
        'tid': tid,
        'category': category
    };

    return body;
}

// 定义执行方法
function do_it() { // 告警记录查询事件
        /* The event.
         */
        $.ajax({
            type: 'post',
            url: 'http://test.ichebao.net/testwspush',
            data: JSON.stringify(get_request()),
            dataType: 'json',
            cache: false,
            contentType: 'application/json; charset=utf-8',
            complete: function(data) {
                console.log("complete:  ", data);
            },

            success: function(data) {
                console.log("success:  ", data);
                if (data.status == 0) {
                    console.log("success  200  ", data);
                } else if (data.status == 403 || data.status == 24) {
                    console.log("success  403   ", data);
                }
            },
            error: function(XMLHttpRequest) {
                console.log("failed     ", XMLHttpRequest);
                return;
            }
        });

    }
    // 绑定方法： 
$('#login_bt').unbind('click').click(do_it);