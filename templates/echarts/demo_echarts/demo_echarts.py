
import sys
sys.path.append('..')       # 相当于cd .. 返回上一级目录，也就可以调用那边的文件了

import os
import shutil
import config
import threading
import numpy as np
import pandas as pd
import myutils.db_one as mmp
import myutils.dict_json_saver as mdjs

from exts import db
from models import User
from flask import json, jsonify
from flask import Flask, render_template, request, redirect, Response, Blueprint
from jinja2 import Environment, FileSystemLoader
from flask_login import UserMixin, login_user, logout_user, login_required, LoginManager, current_user

from colour import Color


env = Environment(loader = FileSystemLoader("./"))
MOD = mmp.MysqlOneDatabase(host=config.host, port=int(config.port), user=config.user, password=config.password, db=config.db)
demo_echarts = Blueprint('demo_echarts', __name__, template_folder='../templates')


@demo_echarts.route('/')
def hello_world():
    print('hello world')
    return 'hello demo_echarts'

# /demo_echarts/json_file?file_name=bar
@demo_echarts.route('/json_file')
def json_file():
    file_name = request.args.get('file_name')
    with open('templates/echarts/demo_echarts/template_hd/%s.json'%file_name,'r', encoding='utf8')as fp: mydict = json.load(fp)
    return jsonify(mydict)

@demo_echarts.route('/json_map')
def json_map():
    file_name = request.args.get('file_name')
    with open('templates/echarts/demo_echarts/json_map/%s.json'%file_name,'r', encoding='utf8')as fp: mydict = json.load(fp)
    return jsonify(mydict)


@demo_echarts.route('/demo_html')
def demo_html():
    file_name = request.args.get('file_name')
    ad = {
    'user_role':current_user.__dict__.get('role'),
    'menu'+'Echarts示例':"menu-open",
    'Echarts示例':"active",
    file_name:"active",
    }    
    return render_template('echarts/demo_echarts/template_hd/%s.html'%file_name, ad=ad)

@demo_echarts.route('/bar')
def bar():
    ############# 读取调整df中的数据
    df = pd.read_csv('templates/echarts/demo_echarts/data/titanic.csv').fillna(0).sort_values('Fare', ascending=False)[:30].reset_index(drop=True)
    ############# 配置参数
    name_col = 'Name'
    data_col = 'Fare'
    fig_type = 'bar'  # 可以设置成bar或者line

    ########### 生成json
    mydict = {}
    mydict['k_list'] = df[name_col].tolist()
    mydict['v_list'] = df[data_col].tolist()
    mydict['fig_type'] = fig_type
    ### 增加颜色
    red = Color("red")
    colors = list(red.range_to(Color("lightgreen"),len(mydict['v_list'])))
    print(colors)
    mydict['c_list'] = []
    for i in range(len(mydict['v_list'])): 
        mydict['c_list'].append(str(colors[i]))
    return jsonify(mydict)

@demo_echarts.route('/pie')
def pie():
    ############# 读取调整df中的数据
    df = pd.read_csv('templates/echarts/demo_echarts/data/titanic.csv').fillna(0).sort_values('Fare', ascending=False)[:10].reset_index(drop=True)
    ############# 配置参数
    name_col = 'Name'
    data_col = 'Fare'
    title = 'Titanic Fare Pie Test'
    radius = ['20%', '85%']
    roseType = 'area'
    ########### 生成json
    mydict = {"title":title}
    data_dict_list = [{"value":df[data_col][i], "name":df[name_col][i]} for i in range(df.shape[0])]
    mydict['data'] = data_dict_list
    mydict['radius'] = radius
    mydict['roseType'] = roseType
    return jsonify(mydict)

@demo_echarts.route('/bar_group')
def bar_group():
    ############# 读取调整df中的数据
    df = pd.read_csv('templates/echarts/demo_echarts/data/titanic.csv').fillna(0).sort_values('Name')[:20]
    df['Pclass'] =  df['Pclass']*10
    stack = None            # 是否堆积
    areaStyle = None        # 是否是面积图    
    ############# 配置参数
    name_col = 'Name'
    data_col_list = 'Fare,Pclass,Age'.split(',')
    fig_type = 'bar'        # 选择柱状图或者折线图: bar/line
    stack = True            # 是否堆积
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

@demo_echarts.route('/sankey')
def sankey():
    ############# 读取调整df中的数据
    df = pd.read_csv('templates/echarts/demo_echarts/data/titanic.csv')
    ############# 配置参数
    cols_list = 'Sex,Pclass,Embarked,SibSp,Parch'.split(',')  # 分类列
    num_col = 'Fare'  # 数值列
    mytitle = 'Titanic船票价格sankey图'

    ############ 生成json
    df = df[cols_list+[num_col]]  # 选择需要的字段
    df[num_col] = df[num_col].fillna(0).astype(int)  # 将数字列fillna
    df = df.sort_values(cols_list).reset_index(drop=True)

    nodes = []
    node_count = 0
    unique_col_dict = {}  # 保存每一列的唯一值
    appear_list = []
    for col in cols_list:
        # unique_col_dict[col] = []
        df[col]=col+'_'+df[col].astype(str)  # 填充缺失的分类列

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
    mydict['title'] = mytitle
    mydict['sub_title'] = num_col+':'+'->'.join(cols_list)
    return jsonify(mydict)

@demo_echarts.route('/map_heat_shanghai')
def map_heat_shanghai():
    ############# 读取调整df中的数据
    df = pd.read_excel('templates/echarts/demo_echarts/data/shanghai_economy_district.xlsx')
    ############# 配置参数
    name_col = '名称'    # 区名列
    year_col = '年份'    # 时间列
    val_col = '第一产业'    # value
    map_path = '/demo_echarts/json_map?file_name=shanghai'

    c1 = Color("lightgreen")
    c2 = Color("red")
    c_n = 100

    ############ 生成json
    province_list = ['浦东新区', '闵行区', '杨浦区', '徐汇区', '松江区', '青浦区', '普陀区', '静安区', '金山区', '嘉定区', 
    '黄浦区', '虹口区', '奉贤区', '崇明区', '长宁区', '宝山区']
    revised_name_list = []

    ## pip install python-Levenshtein
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

@demo_echarts.route('/map_heat_china')
def map_heat_china():
    ############# 读取调整df中的数据
    df = pd.read_excel('templates/echarts/demo_echarts/data/china_carbon_output.xlsx').fillna(0)

    ############# 配置参数
    name_col = '名称'    # 区域名称列
    year_col = '年份'    # 时间列
    val_col = '垃圾产量'    # value
    map_path = '/demo_echarts/json_map?file_name=china'
    title = '上海热力图测试'

    c1 = Color("lightgreen")
    c2 = Color("red")
    c_n = 100
    ############ 生成json
    province_list = '北京市,天津市,上海市,重庆市,河北省,山西省,辽宁省,吉林省,黑龙江省,江苏省,浙江省,安徽省,福建省,江西省,山东省\
    ,河南省,湖北省,湖南省,广东省,海南省,四川省,贵州省,云南省,陕西省,甘肃省,青海省,台湾省,内蒙古自治区,广西壮族自治区,西藏自治区,宁夏回族自治区,\
    ,新疆维吾尔自治区,香港特别行政区,澳门特别行政区'.split(',')
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
        "title":title, 
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
