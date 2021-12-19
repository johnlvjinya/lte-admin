
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

paozhao_schedule = Blueprint('paozhao_schedule', __name__, template_folder='../templates')


@paozhao_schedule.route('/')
def hello_world():
    print('hello world')
    return 'paozhao_schedule hello world'

@paozhao_schedule.route('/cureent_json_html')
@login_required
def cureent_json_html():
    ad = {
        'user_role':USER_ROLE_DICT.get(current_user.username),
        "工单数据":'active',
        "T100大数据分析":'active',
        "menuT100大数据分析":'menu-open',
    }
    file_path = request.args.get('file_path')
    return render_template('dw_cy/paozhao_schedule/%s'%file_path, ad=ad)

@paozhao_schedule.route('/work_process')
def work_process():
    ad = {
        'user_role':USER_ROLE_DICT.get(current_user.username),
        "泡罩数据和算法":'active',
        "泡罩专属排产":'active',
        "menu泡罩专属排产":'menu-open',
    }
    s_str = 'prj_create_t,last_refresh_t,prj_run_error_text,prj_run_state_text'
    sql = '''
    SELECT %s from scheduling_projects____prj_main
    where prj_name='泡罩专属-勿删'
    '''%s_str
    rows = MOD.sql_select_all(sql)
    prj_state_dict = dict(zip(s_str.split(','), list(rows[0])))
    c_time = datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%dT%H:%M') # 2021-10-09T10:08
    print('c_time==========================================', c_time)
    return render_template('dw_cy/paozhao_schedule/paozhao_index.html', ad=ad, prj_state_dict=prj_state_dict, c_time=c_time)

@paozhao_schedule.route('/refresh_download_data', methods=["GET", "POST"])
def refresh_download_data():

    ################################################################## 查工单
    sql = '''
    SELECT distinct(c01_p_product_id) from scheduling_projects_input2_process where prj_name='泡罩专属-勿删'
    '''
    rows = MOD.sql_select_all(sql)
    m_list = [i[0] for i in rows]

    ##### 筛选工单表
    COLS_LIST = '单号,生管人员,工单类型,状态码,工单来源,参考原始单号,母工单单号,生产料号,生产数量,预计开工日,预计完工日,成本中心'.split(',')
    sql = '''
    SELECT  t.sfaadocno,t.sfaa002,t.sfaa003,t.sfaastus,t.sfaa005,t.sfaa022,t.sfaa021,t.sfaa010,t.sfaa012,t.sfaa019,t.sfaa020,t.sfaa068
     from 
    sfaa_t  t 
    where t.sfaastus in ('N','Y') and t.sfaa010 in %s
    '''%str(tuple(m_list))
    cur.execute(sql)
    result = cur.fetchall()
    df1 = pd.DataFrame(result, columns=COLS_LIST)        



    ################################################################## 查订单
    sql = '''
    SELECT distinct(c03_son_product_id) from scheduling_projects_input2_process where prj_name='泡罩专属-勿删'
    '''
    rows = MOD.sql_select_all(sql)
    m_list = [i[0] for i in rows]

    select_cols_dict = {
    'xmdddocno':'订单号',
    'xmdd001':'产品编号',
    'xmdd011':'订单交期',
    'xmdd005':'订单数量',
    'xmdd014':'完工数量',
    }

    s_cols = ','.join(select_cols_dict.keys())
    cn_cols = ','.join(select_cols_dict.values())

    a = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
    b = pd.to_datetime(a) + pd.Timedelta(days=-10)
    # to_date(to_char(time, 'yyyy-MM-dd'), 'yyyy-mm-dd')  
    sql = '''
    SELECT %s from xmdd_t
    WHERE xmdd001 in %s and (xmdd014='0') and xmdd011>to_date('%s','yyyy-mm-dd hh24:mi:ss')
    '''%(s_cols, str(tuple(m_list)), str(b))

    cur.execute(sql)
    result = cur.fetchall()
    df2 = pd.DataFrame(result, columns=cn_cols.split(','))
    # 订单优先级 订单分类    计划开始时间  计划结束时间  订单状态    实际开始时间  实际结束时间  备注
    cl_strr = '接单日期,客户,产品分类,产品属性,是否纳入计划,快捷编号,粒数,物料状态,缺货料号,预计到货时间,订单优先级,订单分类,计划开始时间,计划结束时间,订单状态,实际开始时间,实际结束时间,备注'
    for col in cl_strr.split(','):
        df2[col] = ''
    writer=pd.ExcelWriter('mytemp/泡罩专属-勿删-算法数据导出.xlsx')   

    df1.to_excel(writer,sheet_name='客户工单',index=False)
    df2.to_excel(writer,sheet_name='客户订单',index=False)

    sub_tb_list = 'scheduling_projects_input2_process-scheduling_projects_input3_person-scheduling_projects_input4_person_holiday-scheduling_projects_input5_device-scheduling_projects_input6_bom-scheduling_projects_input7_material-scheduling_projects_input8_calender-scheduling_projects_input9_workmode'.split('-')
    for tb_name in sub_tb_list:
        tb_info = db_info.get(tb_name)
        en_list = []
        cn_list = []
        for i in tb_info:
            if i['name'] not in ['prj_name', 'd_insert_t']:
                en_list.append(i['name'])
                cn_list.append(i['comment'])
        col_str = ','.join(en_list)
        prj_name = '泡罩专属-勿删'
        sql = '''
        select %s from %s where prj_name='%s';
        '''%(col_str, tb_name, prj_name)

        rows = MOD.sql_select_all(sql)
        df = pd.DataFrame(rows, columns=cn_list)
        df.to_excel(writer,sheet_name=tb_cn_en_name.get(tb_name),index=False)    
    writer.save() 

    response = make_response(
        send_from_directory('mytemp', '泡罩专属-勿删-算法数据导出.xlsx', as_attachment=True))
    return response


@paozhao_schedule.route('/run_paozhao_schedule', methods=["GET", "POST"])
def run_paozhao_schedule():
    try:
        prj_name = '泡罩专属-勿删'
        request_form = request.form
        print(prj_name, request_form)
        start_run_time = request.form.get('start_run_time')
        start_run_period = request.form.get('start_run_period')
        solve_max_time = request.form.get('solve_max_time')

        if start_run_time=='':
            flash('请输入开始时间！！')
            return redirect(request.referrer)   # 执行完函数后，返回原来的位置 

        if os.path.exists('templates/dw_cy/paozhao_schedule/algorithm/泡罩专属-勿删-算法数据导出.xlsx') is False:
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

        process = subprocess.Popen(config.python+
            ' templates/dw_cy/paozhao_schedule/algorithm/hun_pai_main.py'+
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
            ' templates/dw_cy/paozhao_schedule/algorithm/s03_create_gannt_json.py')
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
        UPDATE scheduling_projects____prj_main SET prj_run_state_text='运行成功',last_refresh_t='%s'
        where prj_name='%s'; 
        '''%(datetime.datetime.strftime(datetime.datetime.now(),'%Y-%m-%d %H:%M:%S'), prj_name)
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


@paozhao_schedule.route('/result_excel', methods=["GET", "POST"])
def result_excel():
    response = make_response(
        send_from_directory('templates/dw_cy/paozhao_schedule/algorithm', '智能排产结果.xlsx', as_attachment=True))
    return response

