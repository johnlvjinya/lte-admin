
import sys
sys.path.append('..')       # 相当于cd .. 返回上一级目录，也就可以调用那边的文件了

import os
import shutil
import config
import time
import datetime
import pandas as pd
import myutils.db_one as mmp
import myutils.file_list as mfl
import myutils.dict_json_saver as mdjs
from werkzeug.utils import secure_filename          # 使用这个是为了确保filename是安全的

from urllib.parse import urlparse
from urllib import parse

from exts import db
from models import User
from flask import send_file, send_from_directory, json, jsonify, make_response, flash
from flask import Flask, render_template, request, redirect, Response, Blueprint, abort
from flask_login import UserMixin, login_user, logout_user, login_required, LoginManager, current_user
from jinja2 import Environment, FileSystemLoader
import subprocess

from colour import Color


env = Environment(loader = FileSystemLoader("./"))
MOD = mmp.MysqlOneDatabase(host=config.host, port=int(config.port), user=config.user, password=config.password, db=config.db)


with open('myjson/db_info.json', 'r', encoding='utf8')as fp: db_info = json.load(fp)
with open('myjson/all_independent_tb.json', 'r', encoding='utf8')as fp: all_independent_tb = json.load(fp)['all_independent_tb']
with open('myjson/prj_tb_dict.json', 'r', encoding='utf8')as fp: prj_tb_dict = json.load(fp)
with open('myjson/tb_cn_en_name.json', 'r', encoding='utf8')as fp: tb_cn_en_name = json.load(fp)


scheduling_projects = Blueprint('scheduling_projects', __name__, template_folder='../templates')

def parse_url_prj_name():
    parsed_result=urlparse(request.referrer).query
    query_list = parsed_result.split('&')
    q_key_list = [i.split('=')[0] for i in query_list]
    q_val_list = [i.split('=')[1] for i in query_list]
    q_dict = dict(zip(q_key_list, q_val_list))
    print('*'*100, q_dict)
    prj_name = q_dict.get('prj_name')
    prj_name=parse.unquote(prj_name)
    return prj_name  

@scheduling_projects.route('/hello_world')
def hello_world():
    print('hello world')
    return 'scheduling hello world'

@scheduling_projects.route('/prj_detail')
@login_required
def prj_detail():
    ad = {
        'user_role':current_user.__dict__.get('role'),
        "订单排产项目":'active',
        "手工导入排产":'active',
        "menu手工导入排产":'menu-open',
    }   
    prj_name = request.args.get('prj_name')
    tb_name = request.args.get('tb_name')

    if os.path.exists('prj_list/scheduling_projects____prj_main/%s/d_json/last_run_set.json'%prj_name) is True:
        with open('prj_list/scheduling_projects____prj_main/%s/d_json/last_run_set.json'%prj_name,'r', encoding='utf8')as fp:
            last_run_set = json.load(fp)
    else:
        last_run_set = {
          "start_run_time": "",
          "start_run_period": "100",
          "solve_max_time": "20",
        }

    q_str_list = 'prj_create_t,prj_process_text,prj_run_state_text,prj_run_error_text'.split(',')
    sql = '''
    select %s from scheduling_projects____prj_main where prj_name='%s';
    '''%(','.join(q_str_list), prj_name)
    res = MOD.sql_select_one(sql)

    res_dict = dict(zip(q_str_list, list(res)))

    order_delay_hour = 0
    order_finish_date_time = 0
    run_cost_time_second = 0

    return render_template('prj/scheduling_projects/prj_detail.html', prj_name=prj_name,ad=ad,
        prj_create_t=res_dict.get('prj_create_t'),
        prj_process_text=res_dict.get('prj_process_text'),
        prj_run_state_text=res_dict.get('prj_run_state_text'),
        prj_run_error_text=res_dict.get('prj_run_error_text'),

        last_run_set=last_run_set,
        order_delay_hour=order_delay_hour,
        order_finish_date_time=order_finish_date_time,
        run_cost_time_second=run_cost_time_second
        )

@scheduling_projects.route('/prj_data_check')
def prj_data_check():
    print('hello world')
    prj_name = request.args.get('prj_name')

    c_dict_list = []
    for i in range(10):
        dict_test1 = {"c_name":"检查数据内容3_%s"%str(i), "c_result":"出错_%s"%str(i), "c_type":"danger"}
        c_dict_list.append(dict_test1)
    for i in range(5):
        dict_test2 = {"c_name":"检查数据内容_%s"%str(i), "c_result":"没问题！", "c_type":"info"}
        c_dict_list.append(dict_test2)

    ad = {}
    return render_template('prj/scheduling_projects/prj_data_check.html', c_dict_list=c_dict_list, prj_name=prj_name, ad=ad)

@scheduling_projects.route('/prj_data_show')
def prj_data_show():
    prj_name = request.args.get('prj_name')
    ad = {
        'user_role':current_user.__dict__.get('role'),
        "订单排产项目":'active',
        "手工导入排产":'active',
        "menu手工导入排产":'menu-open',
    }
    return render_template('prj/scheduling_projects/prj_data_show.html',c_user=current_user.username,prj_name=prj_name,ad=ad)

@scheduling_projects.route('/order_finish_p')
def order_finish_p():
    mydict = {}
    tb_name = "scheduling_projects____prj_main"
    tb_info = db_info.get(tb_name)
    en_list = [i['name'] for i in tb_info]
    cn_list = [i['comment'] for i in tb_info]
    col_str = ','.join(en_list)
    sql = ''' SELECT COUNT(*) FROM `scheduling_projects____prj_main` WHERE prj_creator='%s';'''%current_user.username
    user_prj_num = MOD.sql_select_one(sql)[0]  # 当前用户创建的项目总数

    if user_prj_num>0:
        sql = ''' 
        SELECT prj_name FROM `scheduling_projects____prj_main` 
        where prj_creator='%s' 
        order by `last_refresh_t` desc; 
        '''%current_user.username
        c_prj = MOD.sql_select_one(sql)[0]

        sql = ''' SELECT c02_customer,c06_id_num,c12_delivery_date,c09_num_need,c10_num_finish 
        FROM `scheduling_projects_input1_order` 
        where prj_name='%s'
        order by c10_num_finish desc
        ; '''%c_prj 
        rows = MOD.sql_select_all(sql)
        df = pd.DataFrame(rows, columns='order_customer,order_product_id,order_delivery_date,order_num_need,order_num_finish'.split(','))
        df['order_num_finish'] = df['order_num_finish'].fillna(0)
        df['order_num_need'] = df['order_num_need'].fillna(100000000)
        df['finish_p'] = 100*df['order_num_finish']/df['order_num_need']
        df['order_name'] = df['order_customer']+'_'+df['order_product_id']+'_'+df['order_delivery_date'].astype(str)+'_'+df['order_num_need'].astype(str)

        mydict['k_list'] = df['order_name'].tolist()
        mydict['v_list'] = [int(i) for i in df['finish_p']]


        red = Color("red")
        colors = list(red.range_to(Color("lightgreen"),101))  
        mydict['c_list'] = []
        for i in range(df.shape[0]): 
            mydict['c_list'].append(str(colors[mydict['v_list'][i]]))
    return jsonify(mydict)

@scheduling_projects.route('/gannt_order')
@login_required
def gannt_order():
    prj_name = request.args.get('prj_name')
    html_name = request.args.get('html_name')
    select_value = request.args.get('select_value')
    print('prj_name, html_name-------------', prj_name, html_name)
    if not html_name:
        with open('prj_list/scheduling_projects____prj_main/%s/d_json/智能排产结果.json'%prj_name,'r', encoding='utf8')as fp:
            mydict = json.load(fp)
        fp.close()
        workline_list = []
        for i in mydict['parkingApron']['data']:
            workline_list.append(i[0])
        workline_list.sort()
        return render_template('prj/scheduling_projects/order_gannt.html', prj_name=prj_name, select_value=select_value,workline_list=workline_list)
    if html_name=="delivery_compare":
        return render_template('prj/scheduling_projects/delivery_compare.html', prj_name=prj_name)
    if html_name=="workline_gannt":
        return render_template('prj/scheduling_projects/workline_gannt.html', prj_name=prj_name)

@scheduling_projects.route('/json_file')
def json_file():
    prj_name = request.args.get('prj_name')
    gannt_type = request.args.get('gannt_type')
    # print('tttttttttt1')
    try:
        if gannt_type=="workline":
            with open('prj_list/scheduling_projects____prj_main/%s/d_json/智能排产结果.json'%prj_name,'r', encoding='utf8')as fp:
                mydict = json.load(fp)
            fp.close()
        if gannt_type=="order":
            with open('prj_list/scheduling_projects____prj_main/%s/d_json/智能排产结果_order.json'%prj_name,'r', encoding='utf8')as fp:
                mydict = json.load(fp)
            fp.close()
        if gannt_type=="delivery_compare":
            print('gannt_type=delivery_compare')
            with open('prj_list/scheduling_projects____prj_main/%s/d_json/delivery_compare.json'%prj_name,'r', encoding='utf8')as fp:
                mydict = json.load(fp)
            fp.close()
            # print(mydict)

    except:
        mydict = {}
    return jsonify(mydict)

@scheduling_projects.route('/delete_prj', methods=["GET", "POST"])
@login_required
def delete_prj():
    
    prj_name = request.args.get('prj_name')
    tb_name = request.args.get('tb_name')
    print('delete_prj',prj_name,tb_name)
    prj_list = os.listdir("prj_list/scheduling_projects____prj_main")
    if prj_name in prj_list:
        print(prj_name)
        shutil.rmtree("prj_list/scheduling_projects____prj_main/%s"%prj_name)
        print("删除成功------------", prj_name)
        sql = '''
        DELETE FROM %s WHERE prj_name='%s' 
        '''%(tb_name, prj_name)
        MOD.sql_excute(sql)
        sql = '''
        SELECT prj_name from scheduling_projects____prj_main
        '''
        sql_prj_list = [i[0] for i in MOD.sql_select_all(sql)]

        sub_tb_list = prj_tb_dict.get('scheduling_projects____prj_main')
        for tb in sub_tb_list:
            sql = '''
            DELETE from %s where prj_name not in %s
            '''%(tb, str(tuple(sql_prj_list)))
            MOD.sql_excute(sql)
        print(sql_prj_list)
        return redirect('/ljy_tb/db_tb?tb_name=scheduling_projects____prj_main')
    else:
        return Response('不存在项目')

@scheduling_projects.route('/set_thisproject_parameters')
@login_required
def set_thisproject_parameters():
    print('hello world---set_thisproject_parameters')
    return redirect(request.referrer)   # 执行完函数后，返回原来的位置  

@scheduling_projects.route('/create_new_prj_post', methods=["GET", "POST"])
@login_required
def create_new_prj_post():
    prj_name = request.args.get('prj_name')
    prj_name = prj_name.replace(' ','')
    prj_name_list = os.listdir('scheduling_prj_list')
    ##################### 检查是否规范
    # if prj_name=='':
    #     print('fafafafffffff1   1')
    #     return Response('项目名不能为空')
    if prj_name in prj_name_list:
        print('fafafafffffff1   2')
        flash('项目已经存在，直接进入项目！')
        return redirect(request.referrer)   # 执行完函数后，返回原来的位置 
    ############## 下面创建文件夹
    
    p_path = "scheduling_prj_list/%s"%prj_name
    if os.path.exists(p_path) is False:os.mkdir(p_path)
    file_list_sub1 = 'data,res_json,res_log'.split(',')
    for path_i in file_list_sub1:
        son_i_path = '%s/%s'%(p_path, path_i)
        if os.path.exists(son_i_path) is False:os.mkdir(son_i_path)

    source = 'scheduling_standard_标准prj目录'
    file_list = os.listdir(source)
    for file in file_list:
        if '.py' in file:
            target = "scheduling_prj_list/%s"%prj_name
            shutil.copy('%s/%s'%(source,file), target)

    # rows = [[prj_name,'10', '项目创建成功', '未运行']]
    # new_col_str = 'prj_name, prj_process, prj_process_text, prj_run_response_text'
    # sql = "insert into {0}({1}) values ({2}) ".format('scheduling_projects', new_col_str, '%s,%s,%s,%s')
    # MOD.sql_insert_excutemany(sql, rows)

    # ############## 保存项目信息的json
    # t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
    # mydict = {"c_time":t, "prj_name":prj_name, "select1":select1, "describe1":describe1}
    # print(mydict, 'mydict====')
    # mdjs.save_dict_to_json(mydict, '%s/res_log/prj_info.json'%p_path)
    flash('创建成功！')
    return redirect(request.referrer)   # 执行完函数后，返回原来的位置 

@scheduling_projects.route('/download_prj_output_excel_post', methods=["GET", "POST"])
@login_required
def download_prj_output_excel_post():
    prj_name = request.args.get('prj_name')
    response = make_response(
        send_from_directory('prj_list/scheduling_projects____prj_main/%s/output'%prj_name, '智能排产结果.xlsx', as_attachment=True))
    return response    

@scheduling_projects.route('/run_scheduling_prj', methods=["GET", "POST"])
@login_required
def run_scheduling_prj():
    try:
        prj_name = request.args.get('prj_name')
        request_form = request.form
        print(prj_name, request_form)
        start_run_time = request.form.get('start_run_time')
        start_run_period = request.form.get('start_run_period')
        solve_max_time = request.form.get('solve_max_time')

        mydict = {
            "start_run_time":start_run_time,
            "start_run_period":start_run_period,
            "solve_max_time":solve_max_time,
        }
        mdjs.save_dict_to_json(mydict, 'prj_list/scheduling_projects____prj_main/%s/d_json/last_run_set.json'%prj_name)

        print('start_run_time,start_run_period.........',start_run_time,start_run_period)
        print(type(start_run_time),type(start_run_period))
        if start_run_time=='':
            flash('请输入开始时间！！')
            return redirect(request.referrer)   # 执行完函数后，返回原来的位置 

        if os.path.exists('prj_list/scheduling_projects____prj_main/%s/output/项目数据导出.xlsx'%prj_name) is False:
            flash('请先同步数据！！')
            return redirect(request.referrer)   # 执行完函数后，返回原来的位置 

        sql = '''
        select prj_run_state_text from scheduling_projects____prj_main 
        where prj_name='%s'; 
        '''%prj_name
        prj_run_response_text = list(MOD.sql_select_one(sql))[0]

        if prj_run_response_text=='正在运行':
            flash('项目正在运行,请耐心等待！！')
            return redirect(request.referrer)   # 执行完函数后，返回原来的位置 
        sql = '''
        update scheduling_projects____prj_main 
        set prj_run_state_text='正在运行', prj_run_error_text='' 
        where prj_name='%s'; 
        '''%prj_name
        MOD.sql_excute(sql)
        flash('开始运行算法')

        process = subprocess.Popen(config.python+
            ' prj_list/scheduling_projects____prj_main/%s/old_main1.py'%prj_name+
            ' --prj_name=%s'%prj_name+
            ' --start_run_time=%s'%start_run_time+
            ' --start_run_period=%s'%start_run_period+
            ' --solve_max_time=%s'%solve_max_time,stderr=subprocess.PIPE
            )
        # print(process.__dict__)
        result = process.wait()
        print('test001', result)

        if result!=0:
            sql = '''
            UPDATE scheduling_projects____prj_main SET prj_process_int='10', 
            prj_run_error_text='排产算法无法执行成功',  
            prj_run_state_text='运行失败'
            where prj_name='%s'; 
            '''%prj_name
            MOD.sql_excute(sql)
            flash('算法报错, 算法程序执行失败')
            return redirect(request.referrer)   # 执行完函数后，返回原来的位置 
        flash('算法运行成功！')


        print("run_scheduling_prj=========test1", prj_name)
        process_2 = subprocess.Popen(config.python+
            ' prj_list/scheduling_projects____prj_main/%s/s03_create_gannt_json.py'%prj_name+
            ' --prj_name=%s'%prj_name)
        result_2 = process_2.wait()


        if result_2!=0:
            sql = '''
            UPDATE scheduling_projects____prj_main SET prj_process_int='60', 
            prj_run_error_text='数据可视化无法执行成功',
            prj_run_state_text='运行失败'
            where prj_name='%s'; 
            '''%prj_name
            MOD.sql_excute(sql)
            flash( '数据可视化数据生成失败！！')
            return redirect(request.referrer)   # 执行完函数后，返回原来的位置 

        print("run_scheduling_prj=========test2", prj_name)
        sql = '''
        UPDATE scheduling_projects____prj_main SET prj_run_state_text='运行成功'
        where prj_name='%s'; 
        '''%prj_name
        MOD.sql_excute(sql)
        flash( '运行成功！')
        return redirect(request.referrer)   # 执行完函数后，返回原来的位置 

    except Exception as e:
        print("run_scheduling_prj=========test4", prj_name)
        run_response_text = "运行失败："+str(e)
        print(run_response_text)
        sql = '''
        UPDATE scheduling_projects____prj_main SET prj_process_int='10', prj_run_state_text='运行失败' 
        where prj_name='%s'; 
        '''%prj_name
        print("run_scheduling_prj=========test5", prj_name)
        MOD.sql_excute(sql)
        flash_text = run_response_text
        flash(flash_text)
        return redirect(request.referrer)   # 执行完函数后，返回原来的位置 

# http://127.0.0.1:5001/file_path?file_name=scheduling/order_finish_process.html
@scheduling_projects.route('/test_order_finish_process')
def test_order_finish_process():

    with open('views_echarts/echarts_data/test/test_order_finish_process.json','r', encoding='utf8')as fp:data = json.load(fp)
    mydict = {"data":data}
    mydict['categories'] = ['categoryA', 'categoryB', 'categoryC']
    mydict['types'] = [
        {"name": 'JS Heap', "color": '#7b9ce1'},
        {"name": 'Documents', "color": '#bd6d6c'},
        {"name": 'Nodes', "color": '#75d874'},
        {"name": 'Listeners', "color": '#e0bc78'},
        {"name": 'GPU Memory', "color": '#dc77dc'},
        {"name": 'GPU', "color": '#72b362'}
    ]
    print(mydict['data'])
    return jsonify(mydict)

# http://127.0.0.1:5001/v_echarts_scheduling/order_sankey
@scheduling_projects.route('/order_sankey')
def order_sankey():
    print('hello world')
    sql = ''' 
    SELECT COUNT(*) FROM `scheduling_projects____prj_main` 
    WHERE prj_creator='%s';
    '''%current_user.username

    prj_total_num = MOD.sql_select_one(sql)[0]

    if prj_total_num>0:
        sql = ''' SELECT prj_name FROM `scheduling_projects____prj_main` 
        WHERE prj_creator='%s'
        order by `last_refresh_t` desc; 
        '''%current_user.username 
        c_prj = MOD.sql_select_one(sql)[0]
    else:
        c_prj = ''

    mydict = {}


    cl_str = 'c03_catagory,c09_num_need,c02_customer,c07_fast_id,c12_delivery_date'
    # cl_str = 'order_catagory,order_product_id,order_delivery_date'
    sql = ''' 
    SELECT %s FROM `scheduling_projects_input1_order`  
    where prj_name='%s';
    '''%(cl_str,c_prj)
    rows = MOD.sql_select_all(sql)
    df = pd.DataFrame(rows, columns=cl_str.split(','))
    d_list = [i.strftime('%Y-%m-%d') for i in df['c12_delivery_date']]
    df['c12_delivery_date'] = d_list
    # df.to_excel('order_sankey.xlsx', index=False)

    color_list = '#5AAEF4,#5B6E96,#FFE88E,#61D9AC,#A8E0FB,#ffdc4c,#fc9850,#e55a55,#6d62e4,#6c9ae7,#4a6fe2,#22c2da'.split(',')
    # df = pd.read_excel('order_sankey.xlsx')    
    num_col = 'c09_num_need'
    df[num_col] = df[num_col].fillna(0)  # 将数字列fillna

    nodes = []
    node_count = 0
    cols_list1 = df.columns.tolist()
    cols_list = [i for i in cols_list1 if i!=num_col]  # 去掉数值列
    df = df.sort_values(cols_list).reset_index(drop=True)
    unique_col_dict = {}  # 保存每一列的唯一值
    appear_list = []
    for col in cols_list:
        # unique_col_dict[col] = []
        df[col]=df[col].fillna(col+'缺失')  # 填充缺失的分类列

        col_unique_list = df[col].unique().tolist()
        col_unique_list = [i for i in col_unique_list if i not in appear_list]
        appear_list += col_unique_list
        unique_col_dict[col]=col_unique_list

        for unique_j in col_unique_list:
            dict_ij = {
                "name":unique_j,
                "color":'#666666',
            }
            nodes.append(dict_ij)


    # print(nodes)
    links = []
    for i in range(len(cols_list)-1):
        col1 = cols_list[i]
        col2 = cols_list[i+1]
        # print('col1, col2', col1, col2)

        for u1 in unique_col_dict[col1]:
            # print('u1', u1)
            for u2 in unique_col_dict[col2]:
                # print('u2', u2)
                dfi_u1_u2 = df[(df[col1]==u1)&(df[col2]==u2)].reset_index(drop=True)
                v = dfi_u1_u2['c09_num_need'].sum()
                if dfi_u1_u2.shape[0]>0:

                    dict_i_u1_u2 = {
                        "source":u1,
                        "target":u2,
                        "value":float(v),
                    }
                    # print(dict_i_u1_u2)
                    links.append(dict_i_u1_u2)


    mydict = {"nodes":nodes, "links":links}
    return jsonify(mydict)

# http://127.0.0.1:5001/v_echarts_scheduling/order_num_bar
@scheduling_projects.route('/data_show')
def data_show():
    prj_name = request.args.get('prj_name')
    return render_template('auto_html/排产数据看板.html',prj_name=prj_name)

# http://127.0.0.1:5001/v_echarts_scheduling/order_num_bar
@scheduling_projects.route('/order_num_bar')
def order_num_bar():
    prj_name = parse_url_prj_name()
    sql = '''
    select order_id_num,order_num_need 
    from scheduling_projects_input1_order 
    where prj_name='%s' order by order_num_need 
    '''%prj_name
    rows = MOD.sql_select_all(sql)

    mydict = {"name_list":[r[0] for r in rows], "data_list":[r[1] for r in rows]}
    # print(mydict)
    return jsonify(mydict)

# http://127.0.0.1:5001/v_echarts_scheduling/order_process_info
@scheduling_projects.route('/order_process_info')
def order_process_info():
    # prj_name = parse_url_prj_name()
    prj_name = "星期六1" # 测试用
    sql = '''
    select order_id_num,order_delivery_date,order_product_id
    from scheduling_projects_input1_order 
    where prj_name='%s'
    '''%prj_name
    rows = MOD.sql_select_all(sql)
    df1 = pd.DataFrame(rows, columns=['order_id_num', 'order_delivery_date', 'order_product_id'])
    print(df1)
    # print(mydict)

    sql = '''
    select p_product_id,f_product_id,son_product_id,product_name
    from scheduling_projects_input2_process 
    where prj_name='%s'
    '''%prj_name
    rows = MOD.sql_select_all(sql)
    df2 = pd.DataFrame(rows, columns='p_product_id,f_product_id,son_product_id,product_name'.split(','))
    print(df2)

    sql = '''
    select work_no,finished_num,order_need_num
    from scheduling_projects_output_1_workno 
    where prj_name='%s'
    '''%prj_name
    rows = MOD.sql_select_all(sql)
    df3 = pd.DataFrame(rows, columns='work_no,finished_num,order_need_num'.split(','))
    print(df3)

    ### 获得测试excel
    writer=pd.ExcelWriter('mytemp/order_test.xlsx')
    df1.to_excel(writer,sheet_name='订单',index=False)
    df2.to_excel(writer,sheet_name='工艺',index=False)
    df3.to_excel(writer,sheet_name='工单',index=False)
    writer.save() 
    writer.close()
    return jsonify({})

