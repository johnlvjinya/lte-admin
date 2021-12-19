import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings("ignore")


plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签
plt.rcParams['font.sans-serif'] = ['Arial']#指定默认字体   
plt.rcParams['axes.unicode_minus']=False #用来正常显示负号

#############################################测试版
# xlsx_path = "input/waste_carbon_platform_v3.xlsx"
# out_xlsx_path = "output/waste_carbon_output.xlsx"%prj_name
#############################################运行版
import sys
import command as tc
cmd_arg = tc.Argument(sys.argv)
prj_name = cmd_arg.get_value("prj_name")
xlsx_path = "prj_list/sjtu_carbon_emission____prj_main/%s/output/项目数据导出.xlsx"%prj_name
out_xlsx_path = "prj_list/sjtu_carbon_emission____prj_main/%s/output/waste_carbon_output.xlsx"%prj_name

df_MSW = pd.read_excel(xlsx_path, sheet_name='区域MSW产量')
df_factor = pd.read_excel(xlsx_path, sheet_name='区域因子')
df_info = pd.read_excel(xlsx_path, sheet_name='区域对应')
df_carbon = pd.read_excel(xlsx_path, sheet_name='区域MSW产量')

columns = '填埋排放,焚烧排放,焚烧净排,生物排放,生物净排,总排放,总净排放,填埋CH4,焚烧CO2,焚烧N2O,焚烧燃料CO2,焚烧发电CO2,堆肥CH4,堆肥N2O,厌氧消化CH4,发电CO2,制肥CO2,回收CO2'.split(',')

a1 = 25
a2 = 298

def search_region(i):
    name = df_carbon['名称'][i]
    region_list = df_info[df_info['地区']==name]['对应'].tolist()
    # print(region)
    return region_list

def select_para(region_list,category):
    if len(region_list)==0:  # 找不到对应地区
        if 'CHN' in df_factor['地区'].tolist():
            para = df_factor[df_factor['地区']=='CHN'][category].tolist()[0]  # 如果有中国的就用中国的数据
        else:
            para = df_factor[category][0].tolist() # 如果没有，就第一行
    else:
        para = None
        priority_list = ['市级','省级','地区级','国家级']  
        for p in priority_list:
            df_p = df_factor[df_factor['地区']==p].reset_index(drop=True)
            for region in region_list:
                if region in df_p['地区'].tolist():
                    para = df_p[df_p['地区']==region][category].tolist()[0]
                    print(para)
                    break
            break
        if not para:
            if 'CHN' in df_factor['地区'].tolist():
                para = df_factor[df_factor['地区']=='CHN'][category].tolist()[0]  # 如果有中国的就用中国的数据
            else:
                para = df_factor[category][0].tolist() # 如果没有，就第一行
    # if 'Shanghai' in region_list:
    #     print(region_list,category, para)
    return para

df_carbon = df_carbon.fillna(0)

for i in range(len(columns)):
    df_carbon[columns[i]] = None

for i in range(df_carbon.shape[0]):
    region = search_region(i)

    df_carbon['填埋CH4'][i] = select_para(region,'填埋CH4')*df_carbon['填埋处理'][i] #https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html
    df_carbon['填埋排放'][i] = df_carbon['填埋CH4'][i]*a1
    df_carbon['焚烧CO2'][i] = select_para(region,'焚烧CO2')*df_carbon['焚烧处理'][i]
    df_carbon['焚烧N2O'][i] = select_para(region,'焚烧N2O')*df_carbon['焚烧处理'][i]
    df_carbon['焚烧燃料CO2'][i] = (select_para(region,'焚烧燃料CO2')+select_para(region,'焚烧燃料CH4')*a1+select_para(region,'焚烧燃料N2O')*a2)*df_carbon['焚烧处理'][i]
    df_carbon['焚烧发电CO2'][i] = select_para(region,'焚烧发电CO2')*df_carbon['焚烧处理'][i]
    df_carbon['焚烧排放'][i] = df_carbon['焚烧CO2'][i]+df_carbon['焚烧N2O'][i]*a2+df_carbon['焚烧燃料CO2'][i]
    df_carbon['焚烧净排'][i] = df_carbon['焚烧排放'][i]-df_carbon['焚烧发电CO2'][i]
    df_carbon['堆肥CH4'][i] = select_para(region,'堆肥CH4')*df_carbon['生物处理'][i]/2
    df_carbon['堆肥N2O'][i] = select_para(region,'堆肥N2O')*df_carbon['生物处理'][i]/2
    df_carbon['厌氧消化CH4'][i] = select_para(region,'厌氧消化CH4')*df_carbon['生物处理'][i]*0.05/2
    df_carbon['发电CO2'][i] = 0.95*select_para(region,'厌氧消化CH4')*df_carbon['生物处理'][i]/2*0.5*50100/3600*select_para(region,'发电CO2')-2.75*select_para(region,'厌氧消化CH4')*df_carbon['生物处理'][i]/2
    df_carbon['制肥CO2'][i] = select_para(region,'制肥CO2')*df_carbon['生物处理'][i]/2
    df_carbon['生物排放'][i] = df_carbon['堆肥CH4'][i]*a1+df_carbon['堆肥N2O'][i]*a2+df_carbon['厌氧消化CH4'][i]*a1
    df_carbon['生物净排'][i] = df_carbon['生物排放'][i]-df_carbon['发电CO2'][i]-df_carbon['制肥CO2'][i]
    df_carbon['回收CO2'][i] = select_para(region,'回收CO2')*df_carbon['回收处理'][i]
    df_carbon['总排放'][i] = df_carbon['填埋排放'][i]+df_carbon['焚烧排放'][i]+df_carbon['生物排放'][i]
    df_carbon['总净排放'][i] = df_carbon['填埋排放'][i]+df_carbon['焚烧净排'][i]+df_carbon['生物净排'][i]-df_carbon['回收CO2'][i]

df_carbon.to_excel(out_xlsx_path, index = False)

# def search_region(i):
#     name = df_carbon['名称'][i]
#     region = df_info[df_info['地区']==name]['区域简写'].tolist()[0]
#     # print(region)
#     return region



