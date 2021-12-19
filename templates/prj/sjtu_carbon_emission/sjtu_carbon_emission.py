
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

sjtu_carbon_emission = Blueprint('sjtu_carbon_emission', __name__, template_folder='../templates')

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

@sjtu_carbon_emission.route('/hello_world')
def hello_world():
    print('hello world')
    return 'scheduling hello world'

@sjtu_carbon_emission.route('/prj_detail')
#@login_required
def prj_detail():
    ad = {
        'user_role':current_user.__dict__.get('role'),
        "MSW碳排放项目":'active',
        "MSW_TPF":'active',
        "menuMSW_TPF":'menu-open',
    }
    prj_name = request.args.get('prj_name')

    q_str_list = 'prj_create_t,prj_process_text,prj_run_state_text,prj_run_error_text'.split(',')
    sql = '''
    select %s from sjtu_carbon_emission____prj_main where prj_name='%s';
    '''%(','.join(q_str_list), prj_name)
    res = MOD.sql_select_one(sql)

    res_dict = dict(zip(q_str_list, list(res)))

    tb_name = 'sjtu_carbon_emission_output1_carbon_emission_result'
    tb_info_ = db_info[tb_name]                                     # tb_name = 'scheduling_projects'
    query_str_list = [i['name'] for i in tb_info_]
    query_str_list_cn = [i['comment'] for i in tb_info_]
    en_cn_dict = dict(zip(query_str_list, query_str_list_cn))

    col_list = ['e'+str(i) for i in range(1, 22)]
    return render_template('prj/sjtu_carbon_emission/prj_detail.html', prj_name=prj_name, ad=ad,
        prj_create_t=res_dict.get('prj_create_t'),
        prj_process_text=res_dict.get('prj_process_text'),
        prj_run_state_text=res_dict.get('prj_run_state_text'),
        prj_run_error_text=res_dict.get('prj_run_error_text'),
        en_cn_dict=en_cn_dict,col_list=col_list,
        year_list=[str(i) for i in range(2010, 2021)],
        )

@sjtu_carbon_emission.route('/prj_data_check')
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
    return render_template('prj/sjtu_carbon_emission/prj_data_check.html', c_dict_list=c_dict_list, prj_name=prj_name, ad=ad)

@sjtu_carbon_emission.route('/index')
def index():
    ad = {
        'user_role':current_user.__dict__.get('role'),
        "MSW碳排放项目":'active',
        "MSW_TPF":'active',
        "menuMSW_TPF":'menu-open',
    }   

    tb_name = "sjtu_carbon_emission____prj_main"
    tb_info = db_info.get(tb_name)
    en_list = [i['name'] for i in tb_info]
    cn_list = [i['comment'] for i in tb_info]
    col_str = ','.join(en_list)

    sql = '''
    select id,%s from %s limit 100;
    '''%(col_str, tb_name)

    res = MOD.sql_select_all(sql)
    rows = [dict(zip(['id']+en_list, [str(j) for j in i])) for i in res]
    print(rows)

    sql = ''' SELECT COUNT(*) FROM `sjtu_carbon_emission____prj_main`; '''
    prj_total_num = MOD.sql_select_one(sql)[0]

    sql = ''' SELECT COUNT(*) FROM `sjtu_carbon_emission____prj_main` WHERE prj_run_state_text='运行成功'; ''' 
    s_total_num = MOD.sql_select_one(sql)[0]

    sql = ''' SELECT COUNT(*) FROM `sjtu_carbon_emission____prj_main` WHERE prj_creator='%s';'''%current_user.username
    user_prj_num = MOD.sql_select_one(sql)[0]  # 当前用户创建的项目总数

    order_list_dict = [] 
    if user_prj_num>0:
        sql = ''' 
        SELECT prj_name FROM `sjtu_carbon_emission____prj_main` 
        where prj_creator='%s' 
        order by `last_refresh_t` desc; 
        '''%current_user.username
        c_prj = MOD.sql_select_one(sql)[0]
        sql = ''' SELECT COUNT(*) FROM `sjtu_carbon_emission_input1_order` where prj_name='%s'; '''%c_prj 
        c_prj_order_num = MOD.sql_select_one(sql)[0]

        sql = ''' SELECT order_customer,order_product_id,order_num_need,order_delivery_date 
        FROM `sjtu_carbon_emission_input1_order` 
        where prj_name='%s'
        order by order_delivery_date desc
        ; '''%c_prj 
        order_list = MOD.sql_select_all(sql)
        
        for o in order_list:
            keys_o = 'order_customer,order_product_id,order_num_need,order_delivery_date'.split(',')
            order_list_dict.append(dict(zip(keys_o,o)))

    else:
        c_prj = ''
        c_prj_order_num = 0

    mydict = {
        "prj_num":prj_total_num, # 项目总数
        "s_total_num":s_total_num, # 成功数量
        "c_prj":c_prj,              # 当前项目
        "c_prj_order_num":c_prj_order_num,
    }
    ad = {
        'user_role':current_user.__dict__.get('role'),
        "MSW碳排放项目":'active',
        "MSW_TPF":'active',
        "menuMSW_TPF":'menu-open',
    }
    return render_template('prj/sjtu_carbon_emission/index.html', rows=rows, cn_list=cn_list, en_list=en_list,
        mydict=mydict,c_user=current_user.username,order_list_dict=order_list_dict, ad=ad)

@sjtu_carbon_emission.route('/json_file')
def json_file():
    prj_name = request.args.get('prj_name')
    gannt_type = request.args.get('gannt_type')
    # print('tttttttttt1')
    try:
        if gannt_type=="workline":
            with open('prj_list/sjtu_carbon_emission____prj_main/%s/d_json/智能排产结果.json'%prj_name,'r', encoding='utf8')as fp:
                mydict = json.load(fp)
            fp.close()
        if gannt_type=="order":
            with open('prj_list/sjtu_carbon_emission____prj_main/%s/d_json/智能排产结果_order.json'%prj_name,'r', encoding='utf8')as fp:
                mydict = json.load(fp)
            fp.close()
        if gannt_type=="delivery_compare":
            print('gannt_type=delivery_compare')
            with open('prj_list/sjtu_carbon_emission____prj_main/%s/d_json/delivery_compare.json'%prj_name,'r', encoding='utf8')as fp:
                mydict = json.load(fp)
            fp.close()
            # print(mydict)

    except:
        mydict = {}
    return jsonify(mydict)

@sjtu_carbon_emission.route('/delete_prj', methods=["GET", "POST"])
#@login_required
def delete_prj():
    prj_long_name = 'sjtu_carbon_emission____prj_main'
    prj_name = request.args.get('prj_name')
    tb_name = request.args.get('tb_name')
    print('delete_prj',prj_name,tb_name)
    prj_list = os.listdir("prj_list/%s"%prj_long_name)
    if prj_name in prj_list:
        print(prj_name)
        shutil.rmtree("prj_list/%s/%s"%(prj_long_name,prj_name))
        print("删除成功------------", prj_name)
        sql = '''
        DELETE FROM %s WHERE prj_name='%s' 
        '''%(tb_name, prj_name)
        MOD.sql_excute(sql)
        sql = '''
        SELECT prj_name from %s
        '''%prj_long_name
        sql_prj_list = [i[0] for i in MOD.sql_select_all(sql)]+['']
        print('sql_prj_list,,,,,,,,,', sql_prj_list)

        sub_tb_list = prj_tb_dict.get(prj_long_name)
        print('sub_tb_list', sub_tb_list)

        for tb in sub_tb_list:
            print('delete.........tb', tb)
            print('tuple(sql_prj_list)............', tuple(sql_prj_list))
            sql = '''
            DELETE from `%s` where prj_name not in %s
            '''%(tb, str(tuple(sql_prj_list)) )
            print('sql=============', sql)
            MOD.sql_excute(sql)
        return redirect('/ljy_tb/db_tb?tb_name=%s'%prj_long_name)
    else:
        return Response('不存在项目')

@sjtu_carbon_emission.route('/download_res_data', methods=["GET", "POST"])
def download_res_data():
    prj_name = request.args.get('prj_name')

    response = make_response(
        send_from_directory('prj_list/sjtu_carbon_emission____prj_main/%s/output'%prj_name, 'waste_carbon_output.xlsx', as_attachment=True))
    return response


@sjtu_carbon_emission.route('/run_prj', methods=["GET", "POST"])
#@login_required
def run_prj():
    try:
        ppp_name = 'sjtu_carbon_emission____prj_main'
        prj_name = request.args.get('prj_name')
        if os.path.exists('prj_list/%s/%s/output/项目数据导出.xlsx'%(ppp_name, prj_name)) is False:
            flash('请先同步数据！！')
            return redirect(request.referrer)   # 执行完函数后，返回原来的位置 
        sql = '''
        select prj_run_state_text from %s
        where prj_name='%s'; 
        '''%(ppp_name, prj_name)
        prj_run_response_text = list(MOD.sql_select_one(sql))[0]

        if prj_run_response_text=='正在运行':
            flash('项目正在运行,请耐心等待！！')
            return redirect(request.referrer)   # 执行完函数后，返回原来的位置 
        sql = '''
        update %s 
        set prj_run_state_text='正在运行', prj_run_error_text='' 
        where prj_name='%s'; 
        '''%(ppp_name, prj_name)
        MOD.sql_excute(sql)
        flash('开始运行算法')

        process = subprocess.Popen(config.python+
            ' prj_list/%s/%s/carbonplatform.py'%(ppp_name, prj_name)+
            ' --prj_name=%s'%prj_name,shell=True
            )
        # print(process.__dict__)
        result = process.wait()
        print('test001', result)

        if result!=0:
            sql = '''
            UPDATE %s SET prj_process_int='10', 
            prj_run_error_text='算法无法执行成功',  
            prj_run_state_text='运行失败'
            where prj_name='%s'; 
            '''%(ppp_name, prj_name)
            MOD.sql_excute(sql)
            flash('算法报错, 算法程序执行失败')


        flash('算法运行成功！')
        sql = '''
        UPDATE %s SET prj_run_state_text='运行成功'
        where prj_name='%s'; 
        '''%(ppp_name, prj_name)
        MOD.sql_excute(sql)

        ########################################### 导入结果
        tb_name = 'sjtu_carbon_emission_output1_carbon_emission_result'
        tb_info_ = db_info[tb_name]                                     # tb_name = 'scheduling_projects'
        query_str_list = [i['name'] for i in tb_info_]
        query_str_list_cn = [i['comment'] for i in tb_info_]

        ffff_name = 'prj_list/%s/%s/output/waste_carbon_output.xlsx'%(ppp_name, prj_name)
        if '.csv' in ffff_name:
            try:
                df = pd.read_csv(ffff_name, encoding='utf-8')
            except:
                try:
                    df = pd.read_csv(ffff_name, encoding='gbk')
                except:
                    df = pd.read_csv(ffff_name, encoding='utf_8_sig')
        elif '.xlsx' in ffff_name:
            try:
                df = pd.read_excel(ffff_name)
            except Exception as e:
                print(e)
        else:
            return jsonify({"code": "error", "message": "{}".format('only accept .xlsx or .csv file')})

        df['导入时间'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        df_columns_list = list(df.columns)
        if prj_name and '项目名' not in df_columns_list:
            df_columns_list.append('项目名')

        if not set(df_columns_list)>=set(query_str_list_cn):  # 导入的excel的字段不够
            lack_list = list(set(query_str_list_cn)-set(df_columns_list))

            df_col_str = ','.join(lack_list)
            print('df_col_str+++++++++++++++++++++++++++++++', df_col_str)
            with open('mytemp/导入字段报错提示.txt', 'w', encoding='utf8') as fp:
                fp.write('导入的excel缺少以下字段：\n')
                fp.write(df_col_str)
            response = make_response(
                send_from_directory('mytemp', '导入字段报错提示.txt', as_attachment=True))
            return response
        if prj_name:
            df['项目名'] = prj_name

        df = df[query_str_list_cn]
        df.columns = query_str_list

        tb_info = db_info.get(tb_name)
        sql = '''
        DELETE from %s where prj_name='%s'
        '''%(tb_name,prj_name)
        MOD.sql_excute(sql)
        ################# 首先删除之前的叔

        for tb_info_j in tb_info:
            if tb_info_j['type'] == 'date' or tb_info_j['type'] == 'datetime':
                df[tb_info_j['name']] = df[tb_info_j['name']].fillna('1900-1-1')

        df = df.fillna('')
        # print(df)
            
        rows = []
        for i in range(df.shape[0]):
            row_i = list(df.iloc[i])
            # print(row_i)
            row_i = [str(j) for j in row_i]
            # for i in row_i:
                # print(type(i))
            rows.append(row_i)
        # sql = """delete from {0}""".format(tb_name)
        # MOD.sql_excute(sql)
        new_col_str = ','.join(query_str_list)                     # 拼接成string
        s_str = '%s,'*len(query_str_list)                             # 拼接 %s 代号
        s_str = s_str.rstrip(',')                                   # 去掉最后一个','
        sql = "insert into {0}({1}) values ({2}) ".format(tb_name, new_col_str, s_str)
        print(sql)
        MOD.sql_insert_excutemany(sql, rows)
        flash('结果写入成功！')
        # except Exception as e:
        #     print('excetp...................', e)
        #     return jsonify({"code": "wrong", "message": "{}".format(e)})        

        return redirect(request.referrer)   # 执行完函数后，返回原来的位置

    except Exception as e:
        run_response_text = "中途失败，原因："+str(e)
        print(run_response_text)
        sql = '''
        UPDATE %s SET prj_process_int='10', prj_run_state_text='运行失败' 
        where prj_name='%s'; 
        '''%(ppp_name, prj_name)
        MOD.sql_excute(sql)
        flash_text = run_response_text
        flash(flash_text)
        return redirect(request.referrer)   # 执行完函数后，返回原来的位置 

@sjtu_carbon_emission.route('/sankey_col', methods=["GET", "POST"])
#@login_required
def sankey_col():
    col_name = request.args.get('col_name')
    num_col = col_name
    prj_name = request.args.get('prj_name')
    ssp = request.args.get('ssp')

    tb_name = 'sjtu_carbon_emission_output1_carbon_emission_result'
    tb_info_ = db_info[tb_name]                                     # tb_name = 'scheduling_projects'
    query_str_list = [i['name'] for i in tb_info_]
    query_str_list_cn = [i['comment'] for i in tb_info_]
    en_cn_dict = dict(zip(query_str_list, query_str_list_cn))

    if not ssp:
        ssp='HD'
    select_str = 'a3_sjtu_ssp,a2_sjtu_year,a1_sjtu_name,%s'%col_name
    cn_select_list = [en_cn_dict.get(i) for i in select_str.split(',')]

    print(select_str, prj_name,ssp)
    sql = '''
    SELECT %s from sjtu_carbon_emission_output1_carbon_emission_result 
    where prj_name='%s' and a3_sjtu_ssp='%s'
    '''%(select_str, prj_name,ssp)
    res = MOD.sql_select_all(sql)

    df = pd.DataFrame(res, columns=select_str.split(','))
    print(df)


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
                v = dfi_u1_u2[num_col].sum()
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

@sjtu_carbon_emission.route('/sankey_col_html', methods=["GET", "POST"])
#@login_required
def sankey_col_html():
    col_name = request.args.get('col_name')
    prj_name = request.args.get('prj_name')
    ssp = request.args.get('ssp')
    tb_name = 'sjtu_carbon_emission_output1_carbon_emission_result'
    tb_info_ = db_info[tb_name]                                     # tb_name = 'scheduling_projects'
    query_str_list = [i['name'] for i in tb_info_]
    query_str_list_cn = [i['comment'] for i in tb_info_]
    en_cn_dict = dict(zip(query_str_list, query_str_list_cn))

    param = {
        "col_name":col_name,
        "prj_name":prj_name,
        "ssp":ssp,
        "col_cn":en_cn_dict.get(col_name)
    }

    ad = {
        'user_role':current_user.__dict__.get('role'),
        "MSW碳排放项目":'active',
        "MSW_TPF":'active',
        "menuMSW_TPF":'menu-open',
    }   
    return render_template('prj/sjtu_carbon_emission/province_year_col_sankey.html', param=param, ad=ad)


@sjtu_carbon_emission.route('/map_heat_china_html', methods=["GET", "POST"])
#@login_required
def map_heat_china_html():
    col_name = request.args.get('col_name')
    prj_name = request.args.get('prj_name')
    ssp = request.args.get('ssp')
    tb_name = 'sjtu_carbon_emission_output1_carbon_emission_result'
    tb_info_ = db_info[tb_name]                                     # tb_name = 'scheduling_projects'
    query_str_list = [i['name'] for i in tb_info_]
    query_str_list_cn = [i['comment'] for i in tb_info_]
    en_cn_dict = dict(zip(query_str_list, query_str_list_cn))

    param = {
        "col_name":col_name,
        "prj_name":prj_name,
        "ssp":ssp,
        "col_cn":en_cn_dict.get(col_name)
    }

    ad = {
        'user_role':current_user.__dict__.get('role'),
        "MSW碳排放项目":'active',
        "MSW_TPF":'active',
        "menuMSW_TPF":'menu-open',
    }   
    return render_template('prj/sjtu_carbon_emission/map_heat_china.html', param=param, ad=ad)

@sjtu_carbon_emission.route('/map_heat_china_col', methods=["GET", "POST"])
#@login_required
def map_heat_china_col():
    col_name = request.args.get('col_name')
    num_col = col_name
    prj_name = request.args.get('prj_name')
    ssp = request.args.get('ssp')

    tb_name = 'sjtu_carbon_emission_output1_carbon_emission_result'
    tb_info_ = db_info[tb_name]                                     # tb_name = 'scheduling_projects'
    query_str_list = [i['name'] for i in tb_info_]
    query_str_list_cn = [i['comment'] for i in tb_info_]
    en_cn_dict = dict(zip(query_str_list, query_str_list_cn))
    # cn_en_dict = dict(zip(query_str_list_cn, query_str_list))

    # ############# 读取调整df中的数据
    df = pd.read_excel('prj_list/sjtu_carbon_emission____prj_main/%s/output/waste_carbon_output.xlsx'%prj_name).fillna(0)

    ############# 配置参数
    name_col = '名称'    # 区域名称列
    year_col = '年份'    # 时间列
    val_col = en_cn_dict.get(num_col)    # value
    map_path = '/demo_echarts/json_map?file_name=china'

    c1 = Color("lightgreen")
    c2 = Color("red")
    c_n = 100
    ############ 生成json
    province_list = '北京市,天津市,上海市,重庆市,河北省,山西省,辽宁省,吉林省,黑龙江省,江苏省,浙江省,安徽省,福建省,江西省,山东省,河南省,湖北省,湖南省,广东省,海南省,四川省,贵州省,云南省,陕西省,甘肃省,青海省,台湾省,内蒙古自治区,广西壮族自治区,西藏自治区,宁夏回族自治区,新疆维吾尔自治区,香港特别行政区,澳门特别行政区'.split(',')
    revised_name_list = []
    p_change_dict = {}
    pv_list = df[name_col].unique().tolist()
    for p in pv_list:
        distance = 0
        sub1_list = ','.join(p).split(',')  # 差分第一个字符
        for stand_p in province_list:
            sub2_list = ','.join(stand_p).split(',')    # 拆分第二个
            inter_sub = set(sub1_list).intersection(set(sub2_list))
            if len(inter_sub)>distance:
                distance = len(inter_sub)
                p0 = stand_p
        p_change_dict[p] = p0
        print(p, ':', p0)
    df[name_col] = df[name_col].map(p_change_dict)  # 根据字典重新对应

    mydict = {
        "map_path":map_path, 
        "data":[], 
        "max_v":int(df[val_col].max()), 
        "min_v":int(df[val_col].min())
        }
    colors = list(c1.range_to(c2, c_n))  # 配置颜色区间
    mydict['c_list'] = [str(colors[i]) for i in range(c_n)]
    unique_year_list = df[year_col].unique().tolist()
    unique_year_list.sort()
    # mydict = {"year_list":unique_year_list}
    for unique_year_i in unique_year_list:
        df_i = df[df[year_col]==unique_year_i].sort_values(val_col).reset_index(drop=True)
        dict_i = {"time":unique_year_i, "data":[]}
        for j in range(df_i.shape[0]):
            dict_ij = {}
            dict_ij['name']=df_i[name_col][j]
            dict_ij['value']=[df_i[val_col][j], df_i[val_col][j], df_i[name_col][j]]
            dict_i['data'].append(dict_ij)
        mydict['data'].append(dict_i)
    return jsonify(mydict)


@sjtu_carbon_emission.route('/bar_group_china_html', methods=["GET", "POST"])
#@login_required
def bar_group_china_html():
    year = request.args.get('year')
    prj_name = request.args.get('prj_name')
    ssp = request.args.get('ssp')
    tb_name = 'sjtu_carbon_emission_output1_carbon_emission_result'
    tb_info_ = db_info[tb_name]                                     # tb_name = 'scheduling_projects'
    query_str_list = [i['name'] for i in tb_info_]
    query_str_list_cn = [i['comment'] for i in tb_info_]
    en_cn_dict = dict(zip(query_str_list, query_str_list_cn))
    param = {
        "prj_name":prj_name,
        "year":year,
        "ssp":ssp,
    }
    ad = {
        'user_role':current_user.__dict__.get('role'),
        "MSW碳排放项目":'active',
        "MSW_TPF":'active',
        "menuMSW_TPF":'menu-open',
    }   
    return render_template('prj/sjtu_carbon_emission/bar_group.html', param=param, ad=ad)

@sjtu_carbon_emission.route('/bar_group_china_col', methods=["GET", "POST"])
#@login_required
def bar_group_china_col():
    year = request.args.get('year')
    prj_name = request.args.get('prj_name')
    ssp = request.args.get('ssp')

    tb_name = 'sjtu_carbon_emission_output1_carbon_emission_result'
    tb_info_ = db_info[tb_name]                                     # tb_name = 'scheduling_projects'
    query_str_list = [i['name'] for i in tb_info_]
    query_str_list_cn = [i['comment'] for i in tb_info_]
    en_cn_dict = dict(zip(query_str_list, query_str_list_cn))
    # cn_en_dict = dict(zip(query_str_list_cn, query_str_list))

    # ############# 读取调整df中的数据
    df = pd.read_excel('prj_list/sjtu_carbon_emission____prj_main/%s/output/waste_carbon_output.xlsx'%prj_name).fillna(0)
    df = df[df['年份']==int(year)].sort_values('填埋处理', ascending=False).reset_index(drop=True)


    stack = None            # 是否堆积
    areaStyle = None        # 是否是面积图    
    ############# 配置参数

    data_col_list = df.columns.tolist()[4:]
    fig_type = 'line'        # 选择柱状图或者折线图: bar/line
    name_col = '名称'
    # stack = True            # 是否堆积
    # areaStyle = True      # 是否是面积图,注意面积图，需要配置：fig_type=line, stack=True 
    ########### 生成json
    mydict = {}

    mydict['xAxis_data'] = df[name_col].tolist()
    mydict['legend_data'] = data_col_list
    mydict['series'] = []
    for col in data_col_list:
        dict_i = {}
        dict_i['name'] = col
        dict_i['type'] = fig_type
        dict_i['emphasis'] = {"focus": "series"}
        if stack:
            dict_i['stack'] = 'yes'
        if areaStyle:
            dict_i['areaStyle'] = {}           
        dict_i['data'] = df[col].tolist()
        mydict['series'].append(dict_i)
    return jsonify(mydict)
