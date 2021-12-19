

import sys
sys.path.append('..')       # 相当于cd .. 返回上一级目录，也就可以调用那边的文件了

import os
import shutil
import config
import time
import datetime
import pandas as pd
import myutils.db_one as mmp
import myutils.dict_json_saver as mdjs

from urllib import parse
from urllib.parse import urlparse
from werkzeug.utils import secure_filename          # 使用这个是为了确保filename是安全的

from exts import db
from models import User
from flask import send_file, send_from_directory, json, jsonify, make_response,url_for, flash
from flask import Flask, render_template, request, redirect, Response, Blueprint, abort
from flask_login import UserMixin, login_user, logout_user, login_required, LoginManager, current_user
from jinja2 import Environment, FileSystemLoader


env = Environment(loader = FileSystemLoader("./"))
MOD = mmp.MysqlOneDatabase(host=config.host, port=int(config.port), user=config.user, password=config.password, db=config.db)
with open('myjson/db_info.json', 'r', encoding='utf8')as fp: db_info = json.load(fp)
with open('myjson/all_independent_tb.json', 'r', encoding='utf8')as fp: all_independent_tb = json.load(fp)['all_independent_tb']
with open('myjson/prj_tb_dict.json', 'r', encoding='utf8')as fp: prj_tb_dict = json.load(fp)
with open('myjson/tb_cn_en_name.json', 'r', encoding='utf8')as fp: tb_cn_en_name = json.load(fp)

prj_main_list = list(prj_tb_dict.keys())  # 所有的项目表

ljy_tb = Blueprint('ljy_tb', __name__, template_folder='../templates')

@ljy_tb.route('/test', methods=['GET','POST'])
@login_required
def test():
    return 'hello-ljy_tb'

# /ljy_tb/db_tb_list
@ljy_tb.route('/db_tb_list', methods=['GET','POST'])
# @login_required
def db_tb_list():
    ad = {
    'user_role':current_user.__dict__.get('role'),
    "表格列表":"active",
    "自动化开发":"active",
    "menu自动化开发":"menu-open",
    }
    sort_dict = {}
    all_independent_tb.sort()
    for k in all_independent_tb:
        sort_dict[k] = db_info[k]
    # for k in db_info.keys():
    #     sort_dict[k] = db_info[k]
    return render_template('ljy_tb/db_tb_list.html', db_info=sort_dict, ad=ad)

@ljy_tb.route('/db_tb', methods=['GET','POST'])
# @login_required
def db_tb():

    tb_name = request.args.get('tb_name')                       # 获得contents
    show_all = request.args.get('show_all')                     # 获得contents
    search_info = request.args.get('search_info')               # 获得contents
    prj_name = request.args.get('prj_name')                     # 获得contents
    sort_d = request.args.get('sort_d')                         # 获得contents
    sort_u = request.args.get('sort_u')                         # 获得contents
    prj_type_short = request.args.get('prj_type_short')
    prj_type = request.args.get('prj_type')

    try:
        if 'scheduling_projects____prj_main' in [tb_name,prj_type]:
            menu_open = "menu手工导入排产"
            menu_active = "手工导入排产"
            tb_active = '订单排产项目'

        elif 'workno_sch_projects____prj_main' in [tb_name,prj_type]:
            menu_open = "menuT100工单排产"
            menu_active = "T100工单排产"
            tb_active = 'T100工单排产项目'

        elif 'sjtu_carbon_emission____prj_main' in [tb_name,prj_type]:
            menu_open = "menuMSW_TPF"
            menu_active = "MSW_TPF"
            tb_active = 'MSW碳排放项目'

        elif tb_name=='auto_sql_bi':
            menu_open = "menu自动化开发"
            menu_active = "自动化开发"
            tb_active = 'SQL_BI列表'

        ad = {
        'user_role':current_user.__dict__.get('role'),
        tb_active:"active",
        menu_active:"active",
        menu_open:"menu-open",
        }
    except:
        ad = {'user_role':current_user.__dict__.get('role'),}


    sub_tb_list_str = request.args.get('sub_tb_list_str')       # 所有的关联子列表
    if sub_tb_list_str:
        sub_tb_list = sub_tb_list_str.split('-')
    else:
        sub_tb_list = []
    # print('db_tb   search_info...........', search_info, sort_d, sort_u)
    # print(sub_tb_list)

    tb_info_ = db_info[tb_name]  # tb_name = 'scheduling_projects'
    # print(tb_info_)
    col_list = [i['name'] for i in tb_info_]
    col_list_cn = [i['comment'] for i in tb_info_]
    col_str = ','.join(col_list)
    # print(col_list)
    # print('*'*100, col_str)
    limit_n = '20'
    if prj_name:
        query_str = "where prj_name='%s' "%prj_name
        limit_n = '5'
    else:
        query_str = ''

    if not search_info:
        if show_all or tb_name in ['auto_sql_bi']:  # 为显示所有，或者为指定表格
            limit_str = ''
        else:
            limit_str = 'LIMIT %s'%limit_n

        en_col_list = [i['name'] for i in tb_info_]
        cn_col_list = [i['comment'] for i in tb_info_]
        cn_en_dict = dict(zip(cn_col_list, en_col_list))

        if sort_u:
            sort_str = 'ORDER BY %s'%cn_en_dict[sort_u]
        elif sort_d:
            sort_str = 'ORDER BY %s DESC'%cn_en_dict[sort_d]
        else:
            sort_str = ''

        # SELECT * FROM `magazine` WHERE CONCAT(`title`,`tag`,`description`) LIKE '%关键字%';

        con_str = ''

        sql = '''
        select id,%s from %s %s %s %s
        '''%(col_str, tb_name,query_str, sort_str, limit_str)

        res = MOD.sql_select_all(sql)
        rows = [dict(zip(['id']+col_list, [str(j) for j in i])) for i in res]        

    else:  # 模糊查询所有字段
        sql = '''
        select id,%s from %s %s
        '''%(col_str, tb_name, query_str)

        res = MOD.sql_select_all(sql)
        rows = []
        for i in res:
            str_i = ''.join(str(i))
            if search_info in str_i:
                rows.append(dict(zip(['id']+col_list, [str(j) for j in i])))

    if tb_name in prj_main_list:
        prj_type = tb_name
        prj_type_short = tb_name.replace('____prj_main','')
        render_str = 'ljy_tb/prj_tb.html'
    else:
        render_str = 'ljy_tb/one_tb.html'

    sub_tb_list1 = []
    for tb in sub_tb_list:
        # print(tb, tb_cn_en_name.get(tb))
        dict_I = {"en":tb}
        if 'output' in tb:
            dict_I['cn'] = '***'+tb_cn_en_name.get(tb)
        else:
            dict_I['cn'] = tb_cn_en_name.get(tb)
        sub_tb_list1.append(dict_I)

    print(prj_type_short, 'hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh')
    return render_template(render_str, 
        rows=rows, col_list_cn=col_list_cn, col_list=col_list,
        tb_name=tb_name, tb_info_=tb_info_,search_info=search_info,
        show_all=show_all,prj_name=prj_name,
        sub_tb_list_str=sub_tb_list_str,
        sub_tb_list=sub_tb_list1,prj_type=prj_type,prj_type_short=prj_type_short,
        tb_name_cn=tb_cn_en_name.get(tb_name), ad=ad,c_user=current_user.__dict__.get('username'),)

@ljy_tb.route('/prj_file_upload_dialog_batch', methods=["GET", "POST"])
# @login_required
def prj_file_upload_dialog_batch():
    print('test'*100)
    parsed_result=urlparse(request.referrer).query
    query_list = parsed_result.split('&')
    
    q_key_list = [i.split('=')[0] for i in query_list]
    q_val_list = [i.split('=')[1] for i in query_list]
    q_dict = dict(zip(q_key_list, q_val_list))
    # print('*'*100, q_dict)
    prj_name = q_dict.get('prj_name')
    prj_name=parse.unquote(prj_name)
    prj_type = q_dict.get('prj_type')


    print('file_upload_dialog_batch')
    print('*'*100, prj_name)
    f = request.files["file"]      
    ffff_name = f.filename                                      # 文件名称
    if ffff_name:
        f.save('prj_list/%s/%s/input/项目输入数据导入.xlsx'%(prj_type, prj_name))
        f.close()
    try:
        for tb in prj_tb_dict.get(prj_type):
            if '_input' in tb: # 输入表
                tb_cn_name = tb_cn_en_name.get(tb) # 得到表的中文名称
                tb_info = db_info.get(tb)
                tb_col_en_list = [i['name'] for i in tb_info]
                tb_col_cn_list = [i['comment'] for i in tb_info]

                df = pd.read_excel('prj_list/%s/%s/input/项目输入数据导入.xlsx'%(prj_type, prj_name), sheet_name=tb_cn_name)

                df['导入时间'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                df_columns_list = list(df.columns)
                if prj_name and '项目名' not in df_columns_list:
                    df_columns_list.append('项目名')

                if not set(df_columns_list)>=set(tb_col_cn_list):  # 导入的excel的字段不够
                    lack_list = list(set(tb_col_cn_list)-set(df_columns_list))
                    df_col_str = ','.join(lack_list)
                    print('df_col_str+++++++++++++++++++++++++++++++', df_col_str)
                    with open('mytemp/导入字段报错提示.txt', 'w', encoding='utf8') as fp:
                        fp.write(tb_cn_name+'======导入的excel缺少以下字段==========\n')
                        fp.write(df_col_str)
                    response = make_response(
                        send_from_directory('mytemp', '导入字段报错提示.txt', as_attachment=True))
                    return response

                df['项目名'] = prj_name
                df = df[tb_col_cn_list]  # 调整次序
                df.columns = tb_col_en_list # 调整表头

                for tb_info_j in tb_info:
                    if tb_info_j['type'] == 'date' or tb_info_j['type'] == 'datetime':
                        df[tb_info_j['name']] = df[tb_info_j['name']].fillna('1900-01-01')
                    if tb_info_j['type'] == 'float' or 'int' in tb_info_j['type']:
                        df[tb_info_j['name']] = df[tb_info_j['name']].fillna(0)                    

                df = df.fillna('')
                # print(df)
                sql = '''
                delete from %s where prj_name='%s';
                '''%(tb, prj_name)
                MOD.sql_excute(sql)

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
                new_col_str = ','.join(tb_col_en_list)                      # 拼接成string
                s_str = '%s,'*len(tb_col_en_list)                           # 拼接 %s 代号
                s_str = s_str.rstrip(',')                                   # 去掉最后一个','
                sql = "insert into {0}({1}) values ({2}) ".format(tb, new_col_str, s_str)
                MOD.sql_insert_excutemany(sql, rows)            
        flash('批量导入成功')

    except Exception as e:
        flash('批量导入失败')
        with open('mytemp/批量导入报错提示.txt', 'w', encoding='utf8') as fp:
            fp.write('导入%s表时报错，请检查该表\n'%tb_cn_name)
            fp.write('导入报错的提示:')
            fp.write(str(e))
        response = make_response(
            send_from_directory('mytemp', '批量导入报错提示.txt', as_attachment=True))
        return response

    return redirect(request.referrer)   # 执行完函数后，返回原来的位置  

@ljy_tb.route('/prj_file_download_dialog_batch', methods=["GET", "POST"])
# @login_required
def prj_file_download_dialog_batch():
    action = request.args.get('action')

    parsed_result=urlparse(request.referrer).query
    query_list = parsed_result.split('&')
    
    q_key_list = [i.split('=')[0] for i in query_list]
    q_val_list = [i.split('=')[1] for i in query_list]
    q_dict = dict(zip(q_key_list, q_val_list))
    # print('*'*100, q_dict)

    prj_name = q_dict.get('prj_name')
    prj_type = q_dict.get('prj_type')
    prj_name=parse.unquote(prj_name)

    sub_tb_list_str = q_dict.get('sub_tb_list_str')
    sub_tb_list = sub_tb_list_str.split('-')

    writer=pd.ExcelWriter('prj_list/%s/%s/output/项目数据导出.xlsx'%(prj_type, prj_name))
    
    for tb_name in sub_tb_list:
        tb_info = db_info.get(tb_name)
        en_list = []
        cn_list = []
        for i in tb_info:
            if i['name'] not in ['prj_name', 'd_insert_t']:
                en_list.append(i['name'])
                cn_list.append(i['comment'])
        col_str = ','.join(en_list)
        sql = '''
        select %s from %s where prj_name='%s';
        '''%(col_str, tb_name, prj_name)

        rows = MOD.sql_select_all(sql)
        df = pd.DataFrame(rows, columns=cn_list)
        df.to_excel(writer,sheet_name=tb_cn_en_name.get(tb_name),index=False)

        
    writer.save() 
    writer.close()
    
    if action=='download_excel':
        flash('数据导出成功！')# 'prj_list/%s/%s/output/项目数据导出.xlsx'%(prj_type, prj_name)
        response = make_response(
            send_from_directory('prj_list/%s/%s/output'%(prj_type, prj_name), '项目数据导出.xlsx', as_attachment=True))
        return response
    if action=='get_algorithm_excel':
        flash('算法数据同步成功！')
        return redirect(request.referrer)   # 执行完函数后，返回原来的位置 

@ljy_tb.route('/prj_tb_list', methods=['GET','POST'])
# @login_required
def prj_tb_list():
    tb_name = request.args.get('tb_name')
    prj_name = request.args.get('prj_name')
    prj_type = request.args.get('tb_name')
    prj_type_short = request.args.get('prj_type_short')
    
    prj_list = prj_tb_dict.get(tb_name)
    # print('tb_name, prj_name', tb_name, prj_name, prj_list)
    sub_tb_list = [i for i in prj_list]
    c_tb = request.args.get('c_tb')  # 当前展示的表格
    if not c_tb:
        c_tb = sub_tb_list[0]
    sub_tb_list_str = '-'.join(sub_tb_list)
    return redirect(url_for('ljy_tb.db_tb',tb_name=c_tb, 
        prj_name=prj_name, 
        sub_tb_list_str=sub_tb_list_str, 
        prj_type=prj_type,
        prj_type_short=prj_type_short
        )
    )

@ljy_tb.route('/db_search', methods=['GET','POST'])
# @login_required
def db_search():
    S = request.values.get('search_str')  # 搜索search_str
    parsed_result=urlparse(request.referrer).query
    query_list = parsed_result.split('&')
    
    q_key_list = [i.split('=')[0] for i in query_list]
    q_val_list = [parse.unquote(i.split('=')[1]) for i in query_list]
    q_dict = dict(zip(q_key_list, q_val_list))
    # print(S, '======', q_dict)
    return redirect(url_for('ljy_tb.db_tb',
        search_info=S, 
        tb_name=q_dict['tb_name'], 
        prj_name=q_dict.get('prj_name'), 
        sub_tb_list_str=q_dict.get('sub_tb_list_str'),
        prj_type=q_dict.get('prj_type'),
        prj_type_short=q_dict.get('prj_type_short')

        ))

@ljy_tb.route('/table_actions', methods=['GET', 'POST'])
# @login_required
def table_actions():

    print('request.method',request.method)
    tb_name = request.args.get('tb_name')                           # 获得contents
    action_name = request.args.get('action_name')                   # 获得contents
    tb_info_ = db_info[tb_name]                                     # tb_name = 'scheduling_projects'
    query_str_list = [i['name'] for i in tb_info_]
    query_str_list_cn = [i['comment'] for i in tb_info_]

    parsed_result=urlparse(request.referrer).query
    query_list = parsed_result.split('&')
    
    q_key_list = [i.split('=')[0] for i in query_list]
    q_val_list = [i.split('=')[1] for i in query_list]
    q_dict = dict(zip(q_key_list, q_val_list))
    # print('*'*100, q_dict)

    prj_name = q_dict.get('prj_name')
    if prj_name:
        prj_name=parse.unquote(prj_name)
        qurey_add_str = '''where prj_name='%s' '''%(prj_name)
    else:
        qurey_add_str = ''

    # print('*'*100, qurey_add_str)
    if action_name == 'download':
        s_str = ','.join(query_str_list)
        sql = '''select %s from %s 
        %s'''%(s_str, tb_name, qurey_add_str)
        values = MOD.sql_select_all(sql)

        df = pd.DataFrame(values, columns=query_str_list_cn)
        tb_name_cn = tb_cn_en_name.get(tb_name)
        if os.path.exists('mytemp/{0}.xlsx'.format(tb_name_cn)):
            os.remove('mytemp/{0}.xlsx'.format(tb_name_cn))
        df.to_excel('mytemp/{0}.xlsx'.format(tb_name_cn), encoding='utf_8_sig', index=False)
        response = make_response(
            send_from_directory('mytemp', '{0}.xlsx'.format(tb_name_cn), as_attachment=True))
        return response
        
    if action_name == 'upload':
        f = request.files["file"]      
        ffff_name = f.filename                                      # 文件名称
        if ffff_name:
            f.save('mytemp/'+ffff_name)
            f.close()
            if '.csv' in ffff_name:
                try:
                    df = pd.read_csv('mytemp/'+ffff_name, encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv('mytemp/'+ffff_name, encoding='gbk')
                    except:
                        df = pd.read_csv('mytemp/'+ffff_name, encoding='utf_8_sig')
            elif '.xlsx' in ffff_name:
                try:
                    df = pd.read_excel('mytemp/'+ffff_name)
                except Exception as e:
                    print(e)
            else:
                return jsonify({"code": "error", "message": "{}".format('only accept .xlsx or .csv file')})
            os.remove('mytemp/'+ffff_name)

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
            # except Exception as e:
            #     print('excetp...................', e)
            #     return jsonify({"code": "wrong", "message": "{}".format(e)})

    if action_name == 'clear':
        sql = '''
        delete from `%s`
        %s
        '''%(tb_name, qurey_add_str)
        try:
            MOD.sql_excute(sql)
        except Exception as e:
            print(e)
    return redirect(request.referrer)   # 执行完函数后，返回原来的位置  

@ljy_tb.route('/table_curd', methods=['GET','POST'])
# @login_required
def table_curd():
    data = json.loads(request.form.get('data'))
    tr_id = data.get('tr_id')
    tb_name = data.get('tb_name')
    action = data.get('action')
    form_data = data.get('form_data')

    print(tb_name, tr_id, action, '.................')    
    if tb_name and tr_id:
        if action=='delete':
            sql = ''' delete from `{0}` where id={1}; '''.format(tb_name, tr_id)
            MOD.sql_excute(sql)
            return {'action':'delete','code':200}

        if action=='update':
            name_list = []
            values_list = []

            for form_i in form_data:
                if form_i.get('value') is not '':
                    name_list.append(form_i.get('name'))
                    values_list.append(form_i.get('value'))
                # else:
                #     name_list.append(form_i.get('name'))
                #     values_list.append('')                    
            print(name_list, values_list)

            str_set = 'set '
            for j in name_list:
                str_set += j + '=%s,'
            str_set = str_set.rstrip(',')
            sql = '''update `{0}` {1} where id={2}; '''.format(tb_name, str_set, tr_id)
            try:
                MOD.sql_excute_values(sql, values_list)
                return jsonify(dict(zip(name_list, values_list)))
            except Exception as e:
                print('excetp...................', e)
                return jsonify({"code": "wrong", "message": "{}".format(e)})

        if action=='add':
            name_list = []
            values_list = []

            for form_i in form_data:
                if form_i.get('value') is not '':
                    name_list.append(form_i.get('name'))
                    values_list.append(form_i.get('value'))
            print(tb_name, prj_main_list)
            if tb_name in prj_main_list:  # 如果这个表示主项目表
                name_list = ['prj_name']
                values_list = [form_i.get('value') for form_i in form_data if form_i.get('name')=='prj_name']
                name_list += ['prj_create_t', 'prj_process_text', 'prj_process_int', 'prj_run_state_text','prj_creator']
                values_list += [time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),'创建成功','10','未运行',current_user.username]
            print(name_list, values_list)
            s_str = '%s,'*len(name_list)
            s_str = s_str.rstrip(',')
            sql = '''insert into `{0}` ({1}) values ({2}); '''.format(tb_name, ','.join(name_list), s_str)
            print(sql)
            MOD.sql_excute_values(sql, values_list)
            return {'action':'delete','code':200}
    else:
        return None

@ljy_tb.route('/table_query/<tb_name>/<tr_id>', methods=['GET','POST'])
# @login_required
def table_query_tb_name_tr_id(tb_name, tr_id):
    tb_info_ = db_info[tb_name]  # tb_name = 'scheduling_projects'
    cols_list = [i['name'] for i in tb_info_]
    s_str = ','.join(cols_list)
    sql = ''' select %s from `%s` where id=%s; '''%(s_str,tb_name,tr_id)
    list_v = list(MOD.sql_select_one(sql))
    print(dict(zip(cols_list, list_v)))
    return  jsonify(dict(zip(cols_list, list_v)))

@ljy_tb.route('/showcols', methods=['GET','POST'])
# @login_required
def showcols():
    data = json.loads(request.form.get('data'))
    tr_id = data.get('tr_id')
    tb_name = data.get('tb_name')
    cols_list_str = data.get('cols_list_str')
    sql = '''select {0} from `{1}` where id='{2}'; '''.format(cols_list_str, tb_name, tr_id)
    res_list = MOD.sql_select_one(sql)
    res_dict = dict(zip(cols_list_str.split(','), res_list))
    # print(res_dict)
    return jsonify(res_dict)


