
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

sql_note_list = Blueprint('sql_note_list', __name__, template_folder='../templates')


@sql_note_list.route('/')
def hello_world():
    print('hello world')
    return 'sql_note_list hello world'

@sql_note_list.route('/s_html', methods=["GET", "POST"])
def s_html():
    print('hello worker_work_order')
    ad = {
        'user_role':USER_ROLE_DICT.get(current_user.username),
        "T100数据查询":'active',
        "T100大数据分析":'active',
        "menuT100大数据分析":'menu-open',
    }   
    if request.method == 'GET':
        return render_template('dw_cy/sql_note_list/sql_note_list.html',ad=ad)


@sql_note_list.route('/worker_work_order', methods=["GET", "POST"])
def worker_work_order():
    gong_hao = request.form['gong_hao']
    workno_select1 = request.form['workno_select1']
    tiao_jian_2 = request.form['tiao_jian_2']

    print(gong_hao, workno_select1, tiao_jian_2)
    if gong_hao is None or gong_hao=='':
        flash('请输入工号')
        return '请输入工号'
    con = cx.connect('fmdsreader/Fmds@2cSz3#@10.1.254.145:10021/topprd')     # 连接数据库
    cur = con.cursor()                                                    # 获得游标            
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

@sql_note_list.route('/erp_stock', methods=["GET", "POST"])
def erp_stock():
    sql = '''
    SELECT
    t.inag001 as 料件编号,
    t.inag009 as 库存数量,
    t.inag018 as 有效日期,
    (case t.inagua001
    when '1' then '合格'
    when '0' then '待检验'
    when '2' then '不合格'
    end
    ) as 质量属性
    from inag_t t 
    where t.inagsite='CY1' and t.inag009>0
    '''

    con = cx.connect('fmdsreader/Fmds@2cSz3#@10.1.254.145:10021/topprd')     # 连接数据库
    cur = con.cursor()                                                    # 获得游标  
    cur.execute(sql)
    result = cur.fetchall()


    df = pd.DataFrame(result, columns='料件编号,库存数量,有效日期,质量属性'.split(','))
    df.to_excel('mytemp/库存料件.xlsx', index=False)
    response = make_response(
        send_from_directory('mytemp', '库存料件.xlsx', as_attachment=True))    
    return response

@sql_note_list.route('/work_process', methods=["GET", "POST"])
def work_process():
    sql = '''
    SELECT
    cpcode as 物料料号,
    cpname as 物料名称,
    capacity as 标准产能,
    qty as 计划人数,
    banqty as 班组长人数,
    (case to_char(machinetype)
    when '01' then '自动'
    when '02' then '半自动'
    when '03' then '手工'
    end
    ) as 设备类型,
    ( case linetype
    when '0' then '罐装'
    when '1' then '包装'
    when '2' then '灌包连线'
    when '3' then '组装'
    end
    ) as 生产方式
    from (select mes_gyline_c.* , row_number() over (PARTITION BY (cpcode || processmode ) 
     order by mes_gyline_c.gylineid desc) as rnum from  mes_gyline_c  ) where rnum=1 
    '''

    con = cx.connect('wms_viewer/Wv#@Ss5qT@10.1.254.145:10058/wmsorcl')     # 连接数据库
    cur = con.cursor()                                                    # 获得游标  
    cur.execute(sql)
    result = cur.fetchall()


    df = pd.DataFrame(result, columns='物料料号,物料名称,标准产能,计划人数,班组长人数,设备类型,生产方式'.split(','))
    df.to_excel('mytemp/工艺路线ALL.xlsx', index=False)
    response = make_response(
        send_from_directory('mytemp', '工艺路线ALL.xlsx', as_attachment=True))    
    return response

@sql_note_list.route('/material_on_the_way', methods=["GET", "POST"])
def material_on_the_way():
    sql = '''
    SELECT
    tdo.pmdodocno as 采购单号,
    tdo.pmdo001 as 料件编号,
    tdo.pmdo006 as 分批采购需求量,
    tdo.pmdo015 as 已收货量,
    tdo.pmdo017 as 仓退换货量,
    tdo.pmdo040 as 仓退量,
    tdo.pmdo019 as 已入库量,
    (tdo.pmdo006-tdo.pmdo019+tdo.pmdo017) as 剩余量,
    tdo.pmdo013 as 倒库日期
    from pmdo_t tdo inner join
    (select  
    tn.pmdndocno,tn.pmdnseq,tn.pmdn001,tn.pmdn006,tn.pmdn007,tn.pmdn014
    from pmdl_t  t  inner join pmdn_t tn on t.pmdldocno=tn.pmdndocno
    where t.pmdlsite='CY1' and t.pmdlstus in('A','Y') and t.pmdlcnfdt>add_months(trunc(sysdate, 'mm'),-18) and tn.pmdn045='1') tno
    on tdo.pmdodocno=tno.pmdndocno and tdo.pmdoseq=tno.pmdnseq
    where tdo.pmdosite='CY1' and (tdo.pmdo006-tdo.pmdo019+tdo.pmdo017) >0
    '''

    con = cx.connect('fmdsreader/Fmds@2cSz3#@10.1.254.145:10021/topprd')     # 连接数据库
    cur = con.cursor()                                                    # 获得游标  
    cur.execute(sql)
    result = cur.fetchall()
    
    df = pd.DataFrame(result, columns='采购单号,料件编号,分批采购需求量,已收货量,仓退换货量,仓退量,已入库量,剩余量,倒库日期'.split(','))
    df.to_excel('mytemp/在途物料.xlsx', index=False)
    response = make_response(
        send_from_directory('mytemp', '在途物料.xlsx', as_attachment=True))    
    return response

@sql_note_list.route('/get_all_template_excel', methods=["GET", "POST"])
def get_all_template_excel():
    max_n = 500
    # df = pd.DataFrame([])
    # df.to_excel('mptemp/erp等数据导出模板.xlsx')
    writer=pd.ExcelWriter('mytemp/erp等数据导出模板.xlsx')

    url_dict = {
        "在途物料":"sql_note_list/material_on_the_way",
        "工艺路线ALL":"sql_note_list/work_process",
        "库存料件":"sql_note_list/erp_stock",

    }
    
    for tb_name in '在途物料,工艺路线ALL,库存料件'.split(','):
        try:
            df = pd.read_excel('mytemp/%s.xlsx'%tb_name)
            df = df[:min(df.shape[0], max_n)]
            df.to_excel(writer,sheet_name=tb_name,index=False)
        except:
            print('需要访问这个路由.........'+url_dict.get(tb_name))

    writer.save() 
    writer.close()

    response = make_response(
        send_from_directory('mytemp', 'erp等数据导出模板.xlsx', as_attachment=True))    
    return response

@sql_note_list.route('/no_process_material', methods=["GET", "POST"])  # 查询没有工艺路线的料件号，并追溯其最近的半年内的订单
def no_process_material():
    print(os.listdir('mytemp'))

    writer=pd.ExcelWriter('mytemp/工艺路线对比表-查缺失工艺的订单料件.xlsx')

    if '工艺路线ALL.xlsx' not in os.listdir('mytemp'):
        work_process()
    df1 = pd.read_excel('mytemp/工艺路线ALL.xlsx')
    df1.to_excel(writer,sheet_name='工艺路线ALL',index=False)

    ############################ 查询订单中的料件编号
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
    b = pd.to_datetime(a) + pd.Timedelta(days=-100)                   # 前一百天的订单，假设延期不能超过100天，超过100天就不用管了
    sql = '''
    SELECT distinct(xmdd001) from xmdd_t
    WHERE xmdd011>to_date('%s','yyyy-mm-dd hh24:mi:ss')
    '''%(str(b))

    # sql = '''
    # SELECT distinct(xmdd001) from xmdd_t
    # '''

    cur.execute(sql)
    result = cur.fetchall()

    df2 = pd.DataFrame(result, columns='料件编号'.split(','))
    df2.to_excel(writer,sheet_name='近100日内的订单料件ALL',index=False)
    

    set1 = set(df1['物料料号'].tolist())    # 工艺料件
    set2 = set(df2['料件编号'].tolist())  # 订单料件

    rows1 = list(set1.intersection(set2)) # 有工艺订单料件
    rows2 = list(set2-set(rows1))  # 无工艺订单料件


    df3 = pd.DataFrame(rows1, columns='有工艺料件'.split(','))
    df3.to_excel(writer,sheet_name='有工艺料件',index=False)

    df4 = pd.DataFrame(rows2, columns='无工艺料件'.split(','))
    df4.to_excel(writer,sheet_name='无工艺料件',index=False)

    writer.save() 
    writer.close()    
    response = make_response(
        send_from_directory('mytemp', '工艺路线对比表-查缺失工艺的订单料件.xlsx', as_attachment=True))    
    return response
