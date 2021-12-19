
function delete_tb_name_tr_id(tb_name, tr_id){

    res = confirm('确认删除?');                 // 确认返回true，否则返回false
    console.log('tr_id........', tr_id);
    if(res){
        var data ={
            data:JSON.stringify({
            'tb_name': tb_name,
            'tr_id':tr_id,
            'action': 'delete'
            })
        };
        console.log('delete_tb_name_tr_id........', data);
        $.ajax({
            url:'/ljy_tb/table_curd',
            type:'POST',
            data: data,                
            success:function(res){
                console.log('ajax post -delete success')
                $('#'+tr_id).remove();               // 删除这行元素
                console.log(res)
            },
            error:function (res) {
                console.log('ajax post -delete fail')
            }
        });
    }else{
        console.log('点击了否') 
    }
}

function clear_tb_action(tb_name, prj_name){
    res = confirm('确认清空所有内容？');                 // 确认返回true，否则返回false
    if(res){
        var data ={
        };
        console.log('delete_tb_name_tr_id........', data);
        $.ajax({
            url:'/ljy_tb/table_actions?tb_name='+tb_name+'&prj_name='+prj_name+'&action_name=clear',
            type:'POST',
            data: data,                
            success:function(res){
                console.log('ajax post -delete success')
                location.replace(location.href);
            },
            error:function (res) {
                console.log('ajax post -delete fail')
            }
        });
    }else{
        console.log('点击了否') 
    }

}



// 点击编辑或新增后，改变dialog中的状态
function update_tb_name_tr_id(tb_name, tr_id, curd_type){
    console.log('fawfea');
    console.log('tb_name, tr_id, curd_type',tb_name, tr_id, curd_type);
    if(curd_type=='update'){    
        var t_color=document.getElementById(tr_id);
        t_color.style.background='azure';
    }
    this.tb_name = tb_name;
    this.tr_id = tr_id;
    this.curd_type = curd_type;

    var data ={
        data:JSON.stringify({
        'tb_name': this.tb_name,
        'tr_id':this.tr_id,
        })
    };
    console.log(data);
    if(curd_type=='update'){
        $.ajax({
            url:'/ljy_tb/table_query/'+this.tb_name+'/'+this.tr_id,
            type:'GET',
            data: data,
            success:function(res){
                console.log('test123', res);
                for(var p in res){//遍历json对象的每个key/value对,p为key
                    // console.log(p + "--->" + res[p]);
                    try {
                        $("#dialog_"+p).attr("value", res[p]);
                    } catch (error) {
                        console.log('没有这个对象')
                    }
                  
                }

            },
            error:function (res){
                console.log('test124', curd_type)
                // closeDialogElementById('update_dialog') 
            }
        });
    }

    showDialogElementById('update_dialog')

}

// action包括 add update
function update_table_submit_do(){
    var data ={
        data:JSON.stringify({
        'tb_name': this.tb_name,
        'tr_id':this.tr_id,
        'action': this.curd_type,
        'form_data': $('#update_submit_form').serializeArray()//.serialize() //.serialize(),// 你的formid
        })
    };
    $.ajax({
        url:'/ljy_tb/table_curd',
        type:'POST',
        data: data,                
        success:function(res){
            console.log('ajax post -update success');
            console.log(res);
            closeDialogElementById('update_dialog');
            location.replace(location.href);
        },
        error:function (res) {
            console.log('ajax post -update fail');
            alert('新增失败',res);
            closeDialogElementById('update_dialog'); 
        }
    });



}

function update_table_submit_cancel(){
    closeDialogElementById('update_dialog')
}






