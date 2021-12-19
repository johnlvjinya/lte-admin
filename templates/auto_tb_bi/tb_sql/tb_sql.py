
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


############ 连接oracle

env = Environment(loader = FileSystemLoader("./"))
MOD = mmp.MysqlOneDatabase(host=config.host, port=int(config.port), user=config.user, password=config.password, db=config.db)


with open('myjson/db_info.json', 'r', encoding='utf8')as fp: db_info = json.load(fp)
with open('myjson/all_independent_tb.json', 'r', encoding='utf8')as fp: all_independent_tb = json.load(fp)['all_independent_tb']
with open('myjson/prj_tb_dict.json', 'r', encoding='utf8')as fp: prj_tb_dict = json.load(fp)
with open('myjson/tb_cn_en_name.json', 'r', encoding='utf8')as fp: tb_cn_en_name = json.load(fp)

tb_sql = Blueprint('tb_sql', __name__, template_folder='../templates')


@tb_sql.route('/')
def hello_world():
    print('hello world')
    return 'tb_sql hello world'

@tb_sql.route('/tb_sql_html', methods=["GET", "POST"])
@login_required
def tb_sql_html():
    ad = {
        'user_role':current_user.get('username'),
        "SQL_BI列表":'active',
        "自动化开发":'active',
        "menu自动化开发":'menu-open',
    }
    c_name = request.args.get('c_name')
    s_str = 'c02_cols_str,c03_sql_str'
    sql = '''
    SELECT %s from auto_sql_bi 
    where c01_name= '%s'
    '''%(s_str, c_name)
    res1 = list(MOD.sql_select_one(sql))
    s_dict = dict(zip(s_str.split(','), res1))

    if request.method == 'GET':
        return render_template('auto_tb_bi/tb_sql/tb_sql.html', ad=ad, s_dict=s_dict, c_name=c_name)

    if request.method == 'POST':
        col_str = request.form['col_str']
        sql_str = request.form['sql_str']
        print(col_str, sql_str)
        if col_str and sql_str:
            ############## 查询字段
            res = MOD.sql_select_all(sql_str)

            df = pd.DataFrame(res)
            if len(col_str.split(','))==df.shape[1]:
                df.columns=col_str.split(',')
            else:
                ccc_list = ['col_'+str(i) for i in range(df.shape[1])]
                df.columns = ccc_list
                col_str = ','.join(ccc_list)

            r_list = []
            for i in range(min(3, df.shape[0])):
                dict_i = {}
                for col_j in col_str.split(','):
                    dict_i[col_j] = df[col_j][i]
                r_list.append(dict_i)

            ############### 更新数据库
            sql = '''
            UPDATE `auto_sql_bi` set c02_cols_str="%s",c03_sql_str="%s" 
            where c01_name="%s" 
            '''%(col_str, sql_str, c_name)

            MOD.sql_excute(sql)
            c_name = request.args.get('c_name')
            s_str = 'c02_cols_str,c03_sql_str'
            sql = '''
            SELECT %s from auto_sql_bi 
            where c01_name= '%s'
            '''%(s_str, c_name)
            res1 = list(MOD.sql_select_one(sql))
            s_dict = dict(zip(s_str.split(','), res1))

            return render_template('auto_tb_bi/tb_sql/tb_sql.html', 
                ad=ad, 
                r_list=r_list, 
                col_list=col_str.split(','),
                s_dict=s_dict, c_name=c_name
                )

        else:
            return render_template('auto_tb_bi/tb_sql/tb_sql.html', ad=ad, s_dict=s_dict, c_name=c_name)
