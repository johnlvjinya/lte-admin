
import sys
sys.path.append('..')       # 相当于cd .. 返回上一级目录，也就可以调用那边的文件了

import os
import shutil
import config
import time
import datetime
import numpy as np
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
from user_role import USER_ROLE_DICT

############ 连接oracle
import cx_Oracle as cx
con = cx.connect('fmdsreader/Fmds@2cSz3#@10.1.254.145:10021/topprd')     # 连接数据库
cur = con.cursor()                                                    # 获得游标

env = Environment(loader = FileSystemLoader("./"))
MOD = mmp.MysqlOneDatabase(host=config.host, port=int(config.port), user=config.user, password=config.password, db=config.db)


with open('myjson/db_info.json', 'r', encoding='utf8')as fp: db_info = json.load(fp)
with open('myjson/all_independent_tb.json', 'r', encoding='utf8')as fp: all_independent_tb = json.load(fp)['all_independent_tb']
with open('myjson/prj_tb_dict.json', 'r', encoding='utf8')as fp: prj_tb_dict = json.load(fp)
with open('myjson/tb_cn_en_name.json', 'r', encoding='utf8')as fp: tb_cn_en_name = json.load(fp)

t100_echarts = Blueprint('t100_echarts', __name__, template_folder='../templates')


@t100_echarts.route('/')
def hello_world():
    print('hello world')
    return 't100_echarts hello world'

@t100_echarts.route('/cureent_json_html')
@login_required
def cureent_json_html():
    ad = {
        'user_role':USER_ROLE_DICT.get(current_user.username),
        "工单数据":'active',
        "T100大数据分析":'active',
        "menuT100大数据分析":'menu-open',
    }
    file_path = request.args.get('file_path')
    return render_template('dw_cy/t100_echarts/%s'%file_path, ad=ad)

@t100_echarts.route('/work_orders')
@login_required
def work_orders():
    ad = {
        'user_role':USER_ROLE_DICT.get(current_user.username),
        "工单数据":'active',
        "T100大数据分析":'active',
        "menuT100大数据分析":'menu-open',
    }   
    return render_template('dw_cy/t100_echarts/work_orders.html', ad=ad)

@t100_echarts.route('/orders')
@login_required
def orders():
    with open('mytemp/t100-订单.json', 'r', encoding='utf8')as fp: res = json.load(fp)
    ad = {
        'user_role':USER_ROLE_DICT.get(current_user.username),
        "订单数据365":'active',
        "T100大数据分析":'active',
        "menuT100大数据分析":'menu-open',
    }   

    return render_template('dw_cy/t100_echarts/orders.html', ad=ad, res=res)

# /t100_echarts/staff_work_order_compare
@t100_echarts.route('/staff_work_order_compare')
@login_required
def staff_work_order_compare():
    col_name = request.args.get('col_name')  #  sfaacrtid: 工号， sfaastus: 状态码

    sql = '''
    SELECT %s,count(*) as num from sfaa_t
    group by %s order by num
    '''%(col_name,col_name)

    cur.execute(sql)
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns='name,v'.split(',')).fillna(0)
    df = df[df['v']>5].reset_index(drop=True)

    mydict = {}

    mydict['k_list'] = df['name'].tolist()
    mydict['v_list'] = df['v'].tolist()
    # print(mydict['v_list'])

    red = Color("red")
    colors = list(red.range_to(Color("lightgreen"),df.shape[0]))  
    mydict['c_list'] = []
    for i in range(df.shape[0]): 
        mydict['c_list'].append(str(colors[i]))

    # print(mydict)
    return jsonify(mydict)

# /t100_echarts/staff_work_order_compare
@t100_echarts.route('/tb_col_classify_compare')
@login_required
def tb_col_classify_compare():
    tb_name = request.args.get('tb_name')  #  sfaacrtid: 工号， sfaastus: 状态码
    col_name = request.args.get('col_name')  #  sfaacrtid: 工号， sfaastus: 状态码
    sort_v = int(request.args.get('sort_v'))
    current_year = request.args.get('current_year')  #  sfaacrtid: 工号， sfaastus: 状态码
    if not sort_v:
        sort_v = 5

    sql = '''
    SELECT %s,count(*) as num from %s
    group by %s order by num
    '''%(col_name, tb_name, col_name)

    cur.execute(sql)
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns='name,v'.split(',')).fillna(0)
    df = df[df['v']>sort_v].reset_index(drop=True)

    mydict = {}

    mydict['k_list'] = df['name'].tolist()
    mydict['v_list'] = df['v'].tolist()
    # print(mydict['v_list'])

    red = Color("red")
    colors = list(red.range_to(Color("lightgreen"),df.shape[0]))  
    mydict['c_list'] = []
    for i in range(df.shape[0]): 
        mydict['c_list'].append(str(colors[i]))

    # print(mydict)
    return jsonify(mydict)

# /t100_echarts/work_order_sankey
@t100_echarts.route('/work_order_sankey')
@login_required
def work_order_sankey():

    mydict = {}

    cl_str = 'sfaacrtdp,sfaacrtid,sfaastus,sfaa068,sfaa010,sfaa012'
    cl_str_cn = '资料录入部门,资料录入者,状态码,成本中心,生产料号,生产数量'

    cl_str = 'sfaastus,sfaacrtid,sfaa068,sfaa012'
    cl_str_cn = '状态码,资料录入者,成本中心,生产数量'

    # cl_str = 'order_catagory,order_product_id,order_delivery_date'
    sql = ''' 
    SELECT %s FROM sfaa_t
    WHERE sfaastus='N' or sfaastus='Y'
    '''%(cl_str)
    cur.execute(sql)
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=cl_str_cn.split(','))
   
    num_col = '生产数量'
    df[num_col] = df[num_col].fillna(0).astype(int)  # 将数字列fillna

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
                v = dfi_u1_u2['生产数量'].sum()
                if dfi_u1_u2.shape[0]>0:

                    dict_i_u1_u2 = {
                        "source":u1,
                        "target":u2,
                        "value":float(v),
                    }
                    # print(dict_i_u1_u2)
                    links.append(dict_i_u1_u2)


    mydict = {"nodes":nodes, "links":links}
    mydict['worker_list'] = df['资料录入者'].tolist()  # 增加资料录入者
    return jsonify(mydict)

# /t100_echarts/staff_work_order_compare
@t100_echarts.route('/staff_workorder_process_compare')  # 产品料号数据
@login_required
def staff_workorder_process_compare():
    staff_id = request.args.get('staff_id')  #  sfaacrtid: 工号， sfaastus: 状态码
    print('staff_id======================', staff_id)

    cl_str = 'sfaacrtdp,sfaacrtid,sfaastus,sfaa068,sfaa010,sfaa012'
    cl_str_cn = '资料录入部门,资料录入者,状态码,成本中心,生产料号,生产数量'

    cl_str = 'sfaa010,sfaa012'
    cl_str_cn = '生产料号,生产数量'

    sql = '''
    SELECT %s from sfaa_t
    WHERE sfaacrtid='%s' and (sfaastus='N' or sfaastus='Y')
    '''%(cl_str,staff_id)

    cur.execute(sql)
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns='name,v'.split(',')).fillna(0).astype(str)
    df=df.sort_values('name').reset_index(drop=True)
    # print(df)

    mydict = {}

    mydict['k_list'] = df['name'].tolist()
    mydict['v_list'] = df['v'].tolist()
    # print(mydict['v_list'])

    red = Color("red")
    colors = list(red.range_to(Color("lightgreen"),df.shape[0]))  
    mydict['c_list'] = []
    for i in range(df.shape[0]): 
        mydict['c_list'].append(str(colors[i]))

    # print(mydict)
    return jsonify(mydict)


@t100_echarts.route('/t100_sql_form', methods=["GET", "POST"])
def t100_sql_form():
    print('hello t100_sql_form')
    ad = {
        'user_role':USER_ROLE_DICT.get(current_user.username),
        "T100数据查询":'active',
        "T100大数据分析":'active',
        "menuT100大数据分析":'menu-open',
    }   
    if request.method == 'GET':
        return render_template('dw_cy/t100_echarts/t100_sql_form.html',ad=ad)
    if request.method == 'POST':

        gong_hao = request.form['gong_hao']
        workno_select1 = request.form['workno_select1']
        tiao_jian_2 = request.form['tiao_jian_2']

        print(gong_hao, workno_select1, tiao_jian_2)
        if gong_hao is None or gong_hao=='':
            flash('请输入工号')
            return '请输入工号'
            # return render_template('prj/workno_sch_projects/t100_sql_form.html',ad=ad)
            
        en_list = 'sfaacrtdp,sfaadocno,sfaa002,sfaa003,sfaa010,sfaa012,sfaa013,sfaa019,sfaa020,sfaa049,sfaa050,sfaa068,sfaa069,sfaaua001'.split(',')
        cn_list = '资料录入部门,单号,生管人员,工单类型,生产料号,生产数量,生产单位,预计开工日,预计完工日,已发料套数,已入库合格量,成本中心,可供给量,开工单次数'.split(',')
          # 注意 sfaastus N表示未审核，Y表示已审核
        sql = '''
        SELECT %s from sfaa_t
        WHERE sfaacrtid='%s' and (sfaastus='N' or sfaastus='Y')
        '''%(','.join(en_list), gong_hao)
        print('tttttttttttttt1111', sql)
        cur.execute(sql)
        result = cur.fetchall()

        df = pd.DataFrame(result, columns=cn_list)
        if workno_select1 is not None:
            words = workno_select1.split('||')
            df = df.loc[sum(df['单号'].str.contains(word) for word in words)>0]
        print('test1222222222')
        print(df)

        df.to_excel('mytemp/工单查询_%s.xlsx'%gong_hao, index=False)
        response = make_response(
            send_from_directory('mytemp', '工单查询_%s.xlsx'%gong_hao, as_attachment=True))
        return response

